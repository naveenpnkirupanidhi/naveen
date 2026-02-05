"""
SQL Agent Module
Converts natural language queries to SQL and executes them against the company database.
"""

import sqlite3
from openai import OpenAI
from typing import Tuple, List, Any, Optional


class SQLAgent:
    """
    Agent responsible for converting natural language to SQL queries
    and executing them against the company database.
    """

    def __init__(self, api_key: str, db_path: str = "company.db"):
        """
        Initialize the SQL Agent.

        Args:
            api_key: OpenAI API key
            db_path: Path to the SQLite database
        """
        self.api_key = api_key
        self.db_path = db_path
        self.client = OpenAI(api_key=api_key)

    def get_schema(self) -> str:
        """
        Returns the database schema for context.
        """
        return """
        Database Schema:

        Table: employees
        Columns:
        - id (INTEGER PRIMARY KEY)
        - name (TEXT) - Employee full name
        - department (TEXT) - Department name
        - salary (REAL) - Annual salary
        - hire_date (TEXT) - Date hired (YYYY-MM-DD)
        - email (TEXT) - Employee email

        Table: departments
        Columns:
        - id (INTEGER PRIMARY KEY)
        - name (TEXT) - Department name
        - budget (REAL) - Annual department budget
        - manager_id (INTEGER) - ID of department manager

        Table: projects
        Columns:
        - id (INTEGER PRIMARY KEY)
        - name (TEXT) - Project name
        - department (TEXT) - Owning department
        - budget (REAL) - Project budget
        - start_date (TEXT) - Start date (YYYY-MM-DD)
        - status (TEXT) - Current status (Planning/In Progress/Completed)
        """

    def generate_sql(self, question: str) -> str:
        """
        Uses GPT to convert a natural language question to SQL.

        Args:
            question: Natural language question about the database

        Returns:
            SQL query string
        """
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a SQL expert. Use this schema:
{self.get_schema()}

Return ONLY the SQL query without any explanation or markdown formatting.
Always use proper SQL syntax for SQLite.
For aggregations, always include meaningful column aliases."""
                },
                {
                    "role": "user",
                    "content": f"Generate SQL for: {question}"
                }
            ],
            temperature=0.1
        )

        sql = response.choices[0].message.content.strip()

        # Clean up the SQL query
        sql = sql.replace('```sql', '').replace('```SQL', '').replace('```', '')
        sql_lines = [line.strip() for line in sql.split('\n') if line.strip()]
        sql = ' '.join(sql_lines)

        return sql

    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """
        Validates SQL query for safety (read-only operations only).

        Args:
            sql: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        sql_lower = sql.lower()
        dangerous_keywords = ['drop', 'delete', 'update', 'insert', 'alter', 'truncate', 'create']

        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                return False, f"Query rejected: {keyword.upper()} operations are not allowed"

        return True, ""

    def execute_query(self, sql: str) -> Tuple[List[Any], List[str]]:
        """
        Executes a SQL query and returns results with column names.

        Args:
            sql: SQL query to execute

        Returns:
            Tuple of (results, column_names)
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            return results, column_names
        finally:
            conn.close()

    def format_results(self, results: List[Any], column_names: List[str]) -> str:
        """
        Formats query results into a readable string.

        Args:
            results: Query results
            column_names: Column names from the query

        Returns:
            Formatted string representation
        """
        if not results:
            return "No results found."

        # Calculate column widths
        widths = []
        for i, col in enumerate(column_names):
            col_values = [str(row[i]) for row in results]
            max_width = max(len(col), max(len(v) for v in col_values))
            widths.append(min(max_width, 25))  # Cap at 25 characters

        # Build header
        header = " | ".join(col.ljust(widths[i]) for i, col in enumerate(column_names))
        separator = "-+-".join("-" * widths[i] for i in range(len(column_names)))

        # Build rows
        rows = []
        for row in results:
            formatted_row = []
            for i, value in enumerate(row):
                if isinstance(value, float):
                    # Format currency values
                    if 'salary' in column_names[i].lower() or 'budget' in column_names[i].lower():
                        formatted_value = f"${value:,.2f}"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                formatted_row.append(formatted_value[:widths[i]].ljust(widths[i]))
            rows.append(" | ".join(formatted_row))

        return f"{header}\n{separator}\n" + "\n".join(rows)

    def query(self, question: str) -> dict:
        """
        Main method to process a natural language query.

        Args:
            question: Natural language question

        Returns:
            Dictionary with 'sql', 'results', 'formatted', and 'error' keys
        """
        result = {
            'sql': '',
            'results': [],
            'formatted': '',
            'error': None
        }

        try:
            # Generate SQL
            sql = self.generate_sql(question)
            result['sql'] = sql

            # Validate SQL
            is_valid, error_msg = self.validate_sql(sql)
            if not is_valid:
                result['error'] = error_msg
                return result

            # Execute query
            results, column_names = self.execute_query(sql)
            result['results'] = results

            # Format results
            result['formatted'] = self.format_results(results, column_names)

        except Exception as e:
            result['error'] = f"Query error: {str(e)}"

        return result


# Test the SQL Agent
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from config import OPENAI_API_KEY

    agent = SQLAgent(OPENAI_API_KEY)

    test_questions = [
        "What is the average salary in each department?",
        "Which department has the highest budget?",
        "List all employees earning more than 75000",
        "How many employees are in each department?",
        "What projects are currently in progress?"
    ]

    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print('='*60)
        result = agent.query(question)
        if result['error']:
            print(f"Error: {result['error']}")
        else:
            print(f"SQL: {result['sql']}")
            print(f"\nResults:\n{result['formatted']}")
