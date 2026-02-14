"""
SQLite Query Agent - Project 1.2
Chat with any SQLite database using natural language.
Claude converts your questions to SQL and displays results.
"""

import os
import sqlite3
from pathlib import Path
import streamlit as st
from anthropic import Anthropic

# Initialize Claude client
client = Anthropic()

# ============== DATABASE FUNCTIONS ==============

def get_database_schema(db_path: str) -> str:
    """Extract schema information from SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    schema_info = []
    
    for (table_name,) in tables:
        schema_info.append(f"\n### Table: {table_name}")
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        schema_info.append("| Column | Type | Nullable | Default | Primary Key |")
        schema_info.append("|--------|------|----------|---------|-------------|")
        
        for col in columns:
            cid, name, col_type, notnull, default, pk = col
            nullable = "NO" if notnull else "YES"
            pk_str = "✓" if pk else ""
            default_str = str(default) if default else ""
            schema_info.append(f"| {name} | {col_type} | {nullable} | {default_str} | {pk_str} |")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        schema_info.append(f"\n*{count} rows*")
        
        # Get sample data (first 3 rows)
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
        samples = cursor.fetchall()
        
        if samples:
            col_names = [desc[0] for desc in cursor.description]
            schema_info.append(f"\n**Sample data:**")
            schema_info.append("| " + " | ".join(col_names) + " |")
            schema_info.append("|" + "|".join(["---"] * len(col_names)) + "|")
            for row in samples:
                schema_info.append("| " + " | ".join(str(v) for v in row) + " |")
    
    conn.close()
    return "\n".join(schema_info)


def execute_sql(db_path: str, sql: str) -> tuple[list, list, str | None]:
    """
    Execute SQL query and return results.
    Returns: (columns, rows, error)
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Get rows
        rows = cursor.fetchall()
        
        conn.close()
        return columns, rows, None
        
    except Exception as e:
        return [], [], str(e)


def get_tables_list(db_path: str) -> list[str]:
    """Get list of table names from database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


# ============== CLAUDE FUNCTIONS ==============

def generate_sql_from_question(question: str, schema: str, chat_history: list) -> dict:
    """
    Use Claude to convert natural language to SQL.
    Returns dict with 'sql', 'explanation', and 'confidence'.
    """
    
    system_prompt = f"""You are a SQL expert assistant. Your job is to convert natural language questions into valid SQLite queries.

## Database Schema
{schema}

## Rules
1. ONLY output valid SQLite syntax
2. Always use table and column names exactly as shown in the schema
3. For date comparisons, use SQLite date functions
4. If the question is ambiguous, make reasonable assumptions and explain them
5. If a query cannot be written (e.g., asking about data that doesn't exist), explain why

## Output Format
Always respond in this exact JSON format:
{{
    "sql": "YOUR SQL QUERY HERE",
    "explanation": "Brief explanation of what the query does",
    "confidence": "high/medium/low",
    "assumptions": ["any assumptions made"]
}}

If you cannot generate a valid query, respond with:
{{
    "sql": null,
    "explanation": "Why the query cannot be generated",
    "confidence": "none",
    "assumptions": []
}}
"""

    # Build messages with chat history for context
    messages = []
    for msg in chat_history[-6:]:  # Keep last 6 messages for context
        messages.append(msg)
    
    messages.append({"role": "user", "content": question})
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system_prompt,
        messages=messages
    )
    
    # Parse response
    response_text = response.content[0].text
    
    # Try to extract JSON from response
    import json
    try:
        # Handle case where response might have markdown code blocks
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0]
        else:
            json_str = response_text
        
        result = json.loads(json_str.strip())
        return result
    except:
        # If JSON parsing fails, return the raw response
        return {
            "sql": None,
            "explanation": response_text,
            "confidence": "low",
            "assumptions": []
        }


def explain_results(question: str, sql: str, columns: list, rows: list) -> str:
    """Use Claude to explain the query results in natural language."""
    
    # Format results as text
    if not rows:
        results_text = "No results returned."
    else:
        results_text = f"Columns: {', '.join(columns)}\n"
        results_text += f"Number of rows: {len(rows)}\n"
        # Show first 10 rows
        for i, row in enumerate(rows[:10]):
            results_text += f"Row {i+1}: {row}\n"
        if len(rows) > 10:
            results_text += f"... and {len(rows) - 10} more rows"
    
    prompt = f"""The user asked: "{question}"

This SQL was executed:
```sql
{sql}
```

Results:
{results_text}

Provide a brief, natural language summary of these results (2-3 sentences max). Be specific with numbers."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="SQLite Query Agent",
    page_icon="🗃️",
    layout="wide"
)

st.title("🗃️ SQLite Query Agent")
st.markdown("*Ask questions about your database in plain English*")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "query_history" not in st.session_state:
    st.session_state.query_history = []

# Sidebar - Database Selection
with st.sidebar:
    st.header("⚙️ Database")
    
    # Find available databases
    data_dir = Path("data")
    if data_dir.exists():
        db_files = list(data_dir.glob("*.db")) + list(data_dir.glob("*.sqlite"))
    else:
        db_files = []
    
    # Also check current directory
    db_files += list(Path(".").glob("*.db")) + list(Path(".").glob("*.sqlite"))
    
    if db_files:
        db_options = {f.name: str(f) for f in db_files}
        selected_db_name = st.selectbox("Select Database", list(db_options.keys()))
        db_path = db_options[selected_db_name]
    else:
        db_path = st.text_input("Database Path", value="data/sample_store.db")
    
    if st.button("📊 Load Database", use_container_width=True):
        if Path(db_path).exists():
            st.session_state.db_path = db_path
            st.session_state.schema = get_database_schema(db_path)
            st.session_state.tables = get_tables_list(db_path)
            st.success(f"Loaded: {db_path}")
        else:
            st.error(f"Database not found: {db_path}")
    
    st.divider()
    
    # Show schema if loaded
    if "schema" in st.session_state:
        st.header("📋 Schema")
        with st.expander("View Tables", expanded=True):
            for table in st.session_state.get("tables", []):
                st.code(table)
        
        if st.checkbox("Show Full Schema"):
            st.markdown(st.session_state.schema)
    
    st.divider()
    
    # Query History
    if st.session_state.query_history:
        st.header("📜 History")
        for i, q in enumerate(st.session_state.query_history[-5:]):
            with st.expander(f"{q['question'][:30]}...", expanded=False):
                st.code(q['sql'], language="sql")

# Main content
if "db_path" not in st.session_state:
    st.info("👈 Select a database in the sidebar to get started.")
    
    st.markdown("""
    ### How to use
    
    1. **Load a database** from the sidebar
    2. **Ask questions** in plain English
    3. **Review** the generated SQL
    4. **Execute** and see results
    
    ### Example questions
    
    - "How many customers do we have?"
    - "What are the top 5 products by sales?"
    - "Show me all orders from last month"
    - "Which city has the most customers?"
    - "What's the average order value?"
    """)

else:
    # Chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Ask a Question")
        
        question = st.text_input(
            "Your question",
            placeholder="e.g., How many orders were placed last month?",
            key="question_input"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            generate_btn = st.button("🔍 Generate SQL", use_container_width=True)
        
        with col_btn2:
            clear_btn = st.button("🗑️ Clear Chat", use_container_width=True)
            if clear_btn:
                st.session_state.chat_history = []
                st.session_state.query_history = []
                st.rerun()
    
    with col2:
        st.subheader("📊 Quick Stats")
        if "tables" in st.session_state:
            st.metric("Tables", len(st.session_state.tables))
    
    st.divider()
    
    # Process question
    if generate_btn and question:
        with st.spinner("Claude is thinking..."):
            result = generate_sql_from_question(
                question,
                st.session_state.schema,
                st.session_state.chat_history
            )
        
        st.session_state.current_result = result
        st.session_state.current_question = question
        
        # Add to chat history
        st.session_state.chat_history.append({"role": "user", "content": question})
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": f"SQL: {result.get('sql', 'N/A')}\nExplanation: {result.get('explanation', '')}"
        })
    
    # Display current query
    if "current_result" in st.session_state:
        result = st.session_state.current_result
        question = st.session_state.current_question
        
        st.subheader(f"❓ {question}")
        
        # Show confidence badge
        confidence = result.get("confidence", "unknown")
        if confidence == "high":
            st.success(f"Confidence: {confidence.upper()}")
        elif confidence == "medium":
            st.warning(f"Confidence: {confidence.upper()}")
        else:
            st.error(f"Confidence: {confidence.upper()}")
        
        # Show explanation
        st.markdown(f"**Explanation:** {result.get('explanation', 'N/A')}")
        
        # Show assumptions if any
        assumptions = result.get("assumptions", [])
        if assumptions:
            st.markdown("**Assumptions:**")
            for a in assumptions:
                st.markdown(f"- {a}")
        
        # Show SQL
        sql = result.get("sql")
        if sql:
            st.subheader("📝 Generated SQL")
            st.code(sql, language="sql")
            
            # Execute button
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("▶️ Execute Query", type="primary", use_container_width=True):
                    with st.spinner("Running query..."):
                        columns, rows, error = execute_sql(st.session_state.db_path, sql)
                    
                    if error:
                        st.error(f"SQL Error: {error}")
                    else:
                        st.session_state.last_results = {
                            "columns": columns,
                            "rows": rows,
                            "sql": sql,
                            "question": question
                        }
                        
                        # Add to query history
                        st.session_state.query_history.append({
                            "question": question,
                            "sql": sql
                        })
            
            with col2:
                if st.button("📋 Copy SQL", use_container_width=True):
                    st.write("SQL copied to clipboard!")
                    st.code(sql, language="sql")
        else:
            st.warning("Could not generate a valid SQL query for this question.")
    
    # Display results
    if "last_results" in st.session_state and st.session_state.last_results:
        results = st.session_state.last_results
        
        st.divider()
        st.subheader("📊 Results")
        
        columns = results["columns"]
        rows = results["rows"]
        
        if rows:
            # Create dataframe for display
            import pandas as pd
            df = pd.DataFrame(rows, columns=columns)
            
            st.dataframe(df, use_container_width=True)
            st.caption(f"Showing {len(rows)} rows")
            
            # Natural language summary
            if st.button("🤖 Explain Results"):
                with st.spinner("Claude is analyzing..."):
                    summary = explain_results(
                        results["question"],
                        results["sql"],
                        columns,
                        rows
                    )
                st.info(summary)
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ Download CSV",
                csv,
                "query_results.csv",
                "text/csv"
            )
        else:
            st.info("Query returned no results.")

# Footer
st.divider()
st.caption("Project 1.2 - SQLite Query Agent | learn-agentic-stack")
