# Author: Prof. MM Ghassemi <ghassem3@msu.edu>

import psycopg2
import psycopg2.extras
import glob
import json
import csv
from io import StringIO
import itertools
import hashlib
import os
import cryptography
from cryptography.fernet import Fernet
from math import pow
from flask import current_app
class database:
    """
    Database management class for PostgreSQL operations.
    
    Handles database connections, table creation, data insertion,
    and user authentication with encryption support.
    """

    def __init__(self, purge=False):
        """
        Initialize database connection and configuration.
        
        Args:
            purge (bool): Whether to purge existing tables
        """
        # Grab information from the configuration file
        self.database   = current_app.config.get('DATABASE_NAME')
        self.host       = current_app.config.get('DATABASE_HOST')
        self.user       = current_app.config.get('DATABASE_USER')
        self.port       = current_app.config.get('DATABASE_PORT')
        self.password   = current_app.config.get('DATABASE_PASSWORD')
        
        # Tables must be created in order due to foreign key constraints
        self.tables = ['institutions', 'positions', 'experiences', 'skills', 'users', 'llm_roles', 'benchmark_test_cases', 'benchmark_results']

        # Encryption configuration
        self.encryption = {
            'oneway': {
                'salt': current_app.config.get('ENCRYPTION_ONEWAY_SALT').encode(),
                'n': current_app.config.get('ENCRYPTION_ONEWAY_N'),
                'r': current_app.config.get('ENCRYPTION_ONEWAY_R'),
                'p': current_app.config.get('ENCRYPTION_ONEWAY_P')
            },
            'reversible': { 'key': current_app.config.get('ENCRYPTION_REVERSIBLE_KEY')}
        }

    #--------------------------------------------------
    # DATABASE QUERY FUNCTION
    #--------------------------------------------------
    def query(self, query="SELECT * FROM users", parameters=None):
        """
        Execute a database query with optional parameters.
        
        Args:
            query (str): SQL query to execute
            parameters (tuple, optional): Query parameters for parameterized queries
            
        Returns:
            list: Query results as list of dictionaries
        """
        # Establish database connection
        cnx = psycopg2.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            port=self.port,
            database=self.database
        )

        # Execute query with or without parameters
        if parameters is not None:
            cur = cnx.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(query, parameters)
        else:
            cur = cnx.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(query)

        # Only fetch results for SELECT queries, not for CREATE/DROP/INSERT
        row = []
        if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
            row = cur.fetchall()
        
        # Commit transaction and close connections
        cnx.commit()
        cur.close()
        cnx.close()
        
        return row

    #--------------------------------------------------
    # RESUME DATA FUNCTIONS
    #--------------------------------------------------
    def getResumeData(self):
        data = {}

        # For each institution
        institutions = self.query("SELECT * FROM institutions")
        for i in institutions:
            institution_id = i['inst_id']
            data[institution_id] = i
            data[institution_id].pop('inst_id')

            # For each position
            positions = self.query(f"""SELECT * FROM positions WHERE inst_id = {institution_id} ORDER BY start_date DESC""")
            data[institution_id]['positions'] = {}
            for p in positions:
                position_id = p['position_id']
                data[institution_id]['positions'][position_id] = p
                data[institution_id]['positions'][position_id].pop('position_id')
                data[institution_id]['positions'][position_id].pop('inst_id')

                # For each experience
                experiences = self.query(f"""SELECT * FROM experiences WHERE position_id = {position_id} ORDER BY start_date DESC""")
                data[institution_id]['positions'][position_id]['experiences'] = {}
                for e in experiences:
                    experience_id = e['experience_id']
                    data[institution_id]['positions'][position_id]['experiences'][experience_id] = e
                    data[institution_id]['positions'][position_id]['experiences'][experience_id].pop('experience_id')
                    data[institution_id]['positions'][position_id]['experiences'][experience_id].pop('position_id')

                    # For each skill
                    skills = self.query(f"""SELECT * FROM skills WHERE experience_id = {experience_id}""")
                    data[institution_id]['positions'][position_id]['experiences'][experience_id]['skills'] = {}
                    for s in skills:
                        skill_id = s['skill_id']
                        data[institution_id]['positions'][position_id]['experiences'][experience_id]['skills'][skill_id] = s
                        data[institution_id]['positions'][position_id]['experiences'][experience_id]['skills'][skill_id].pop('experience_id')
                        data[institution_id]['positions'][position_id]['experiences'][experience_id]['skills'][skill_id].pop('skill_id')


        # Convert dates to simple strings before returning
        for inst in data.values():
            for pos in inst['positions'].values():
                if pos['start_date']:
                    pos['start_date'] = str(pos['start_date'])[:7]  # Just take "YYYY-MM" part
                if pos['end_date'] and pos['end_date'] != '0000-00-00':
                    pos['end_date'] = str(pos['end_date'])[:7]
                else:
                    pos['end_date'] = 'Present'
                    
                for exp in pos['experiences'].values():
                    if exp['start_date']:
                        exp['start_date'] = str(exp['start_date'])[:7]
                    if exp['end_date'] and exp['end_date'] != '0000-00-00':
                        exp['end_date'] = str(exp['end_date'])[:7]
                    else:
                        exp['end_date'] = ''
        
        return data

    #--------------------------------------------------
    # TABLE CREATION
    #--------------------------------------------------
    def createTables(self, purge=False, data_path = 'flask_app/database/'):
      
        if purge:
            for table in self.tables[::-1]:
                self.query(f"""DROP TABLE IF EXISTS {table}""")
            
        # Execute all SQL queries in the /database/create_tables directory.
        for table in self.tables:
            
            #Create each table using the .sql file in /database/create_tables directory.
            with open(data_path + f"create_tables/{table}.sql") as read_file:
                create_statement = read_file.read()
            self.query(create_statement)

            # Import the initial data
            try:
                params = []
                with open(data_path + f"initial_data/{table}.csv") as read_file:
                    scsv = read_file.read()            
                for row in csv.reader(StringIO(scsv), delimiter=',', quotechar='"'):
                    # Remove quotes from values if they exist and convert "NULL" to None
                    cleaned_row = []
                    for value in row:
                        if value and value.startswith('"') and value.endswith('"'):
                            value = value.strip('"')
                        if value == "NULL":
                            value = None
                        cleaned_row.append(value)
                    params.append(cleaned_row)
            
                # Insert the data
                cols = params[0]; params = params[1:]

                # Only insert if there is actual data (not just headers)
                if params:
                    # Special handling for users table - encrypt passwords
                    if table == 'users':
                        # Find the password column index
                        password_col_idx = cols.index('password')
                        # Encrypt all passwords in the data
                        for row in params:
                            if row[password_col_idx]:  # Only encrypt if password exists
                                row[password_col_idx] = self.onewayEncrypt(row[password_col_idx])

                    self.insertRows(table = table,  columns = cols, parameters = params)
                    print(f"* Imported data for {table}")
                else:
                    print(f"* No data to import for {table} (empty CSV)")
            except FileNotFoundError:
                print(f"* No CSV file found for {table}")
            except Exception as e:
                print(f"* Error importing data for {table}: {e}")

    def insertRows(self, table='table', columns=['x','y'], parameters=[['v11','v12'],['v21','v22']]):
        
        def process_value(value, query_params):
            """Process a single value, returning placeholder and updating query_params"""
            if isinstance(value, str) and value.strip().startswith('(SELECT'):
                # This is a nested query, insert it directly without parameterization
                return value
            else:
                # Regular parameter, use %s placeholder
                query_params.append(value)
                return '%s'
        
        # Check if there are multiple rows present in the parameters
        has_multiple_rows = any(isinstance(el, list) for el in parameters)
        keys = ','.join(columns)
        query_params = []
        
        # Construct the query we will execute to insert the row(s)
        query = f"""INSERT INTO {table} ({keys}) VALUES """
        
        if has_multiple_rows:
            value_clauses = []
            for p in parameters:
                placeholders = [process_value(value, query_params) for value in p]
                value_clauses.append(f"({','.join(placeholders)})")
            query += ','.join(value_clauses)
        else:
            placeholders = [process_value(value, query_params) for value in parameters]
            query += f"""({','.join(placeholders)}) """                      
        
        # Add RETURNING clause for PostgreSQL to get the inserted ID
        query += " RETURNING *"

        print("Executing query:", query)
        print("With parameters:", query_params)
        
        result = self.query(query, query_params if query_params else None)
        if result and len(result) > 0:
            # Get the first inserted row's ID - try common ID patterns
            insert_id = result[0].get('id') or result[0].get(f'{table[:-1]}_id') or result[0].get(f'{table}_id')
        else:
            insert_id = None         
        return insert_id

    #--------------------------------------------------
    # AUTHENTICATION FUNCTIONS
    #--------------------------------------------------
    def authenticate(self, email='me@email.com', password='password'):
        ''' A function that checks if a given username and password combination exist in the database '''

        # 1. Write a query that checks if a given username and password combination match an entry in the database.
        check = self.query(query      = """SELECT COUNT(*) as success FROM users WHERE email=%s AND password=%s""",
                           parameters = [email, self.onewayEncrypt(password)])[0]
        
        # 2. The function should return a dict that indicates if the authentication check was a success or not, e.g. {'success': 1} or {'success': 0}
        return check 

    def get_user_email(self, session_data=None):
        """Get the current user's email from session data."""
        if session_data is None:
            from flask import session
            session_data = session
        if 'email' in session_data:
            return self.reversibleEncrypt('decrypt', session_data['email'])
        return 'Unknown'

    def get_user_role(self, session_data=None):
        """Get the current user's role from session data."""
        if session_data is None:
            from flask import session
            session_data = session
        if 'email' in session_data:
            email = self.reversibleEncrypt('decrypt', session_data['email'])
            if email != 'Unknown':
                result = self.query("SELECT role FROM users WHERE email=%s", [email])
                if result:
                    role = result[0]['role']
                    return role
        return 'guest'

    #--------------------------------------------------
    # ENCRYPTION FUNCTIONS
    #--------------------------------------------------
    def onewayEncrypt(self, string):
        encrypted_string = hashlib.scrypt(string.encode('utf-8'),
                                          salt = self.encryption['oneway']['salt'],
                                          n    = self.encryption['oneway']['n'],
                                          r    = self.encryption['oneway']['r'],
                                          p    = self.encryption['oneway']['p']
                                          ).hex()
        return encrypted_string

    def reversibleEncrypt(self, type, message):
        fernet = Fernet(self.encryption['reversible']['key'])
        if type == 'encrypt':
            message = fernet.encrypt(message.encode())
        elif type == 'decrypt':
            message = fernet.decrypt(message).decode()

        return message

    #--------------------------------------------------
    # BENCHMARK FUNCTIONS
    #--------------------------------------------------
    def getBenchmarkTestCases(self, category=None, active_only=True):
        """
        Retrieve benchmark test cases from the database.

        Args:
            category: Filter by test category (optional)
            active_only: Only return active tests (default True)

        Returns:
            List of test case dictionaries
        """
        query = "SELECT * FROM benchmark_test_cases WHERE 1=1"
        params = []

        if category:
            query += " AND test_category = %s"
            params.append(category)

        if active_only:
            query += " AND active = TRUE"

        query += " ORDER BY test_id"

        return self.query(query, tuple(params) if params else None)

    def storeBenchmarkResult(self, test_id, agent_response, expected_response,
                             passed, execution_time_ms=None, error_message=None,
                             metadata=None):
        """
        Store a benchmark test result in the database.

        Args:
            test_id: ID of the test case
            agent_response: Actual response from the agent
            expected_response: Expected response for comparison
            passed: Boolean indicating if test passed
            execution_time_ms: Execution time in milliseconds (optional)
            error_message: Error details if test failed (optional)
            metadata: Additional data as JSON (optional)

        Returns:
            Result ID of the stored result
        """
        query = """
            INSERT INTO benchmark_results
            (test_id, agent_response, expected_response, passed,
             execution_time_ms, error_message, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING result_id
        """

        # Convert metadata dict to JSON string if provided
        metadata_json = json.dumps(metadata) if metadata else None

        result = self.query(query, (
            test_id,
            agent_response,
            expected_response,
            passed,
            execution_time_ms,
            error_message,
            metadata_json
        ))

        return result[0]['result_id'] if result else None

    def getBenchmarkMetrics(self, category=None, limit_results=100):
        """
        Get aggregated benchmark metrics.

        Args:
            category: Filter by test category (optional)
            limit_results: Number of recent results to analyze (default 100)

        Returns:
            Dictionary with benchmark metrics
        """
        # Build base query for recent results
        query = """
            SELECT
                br.test_id,
                btc.test_category,
                br.passed,
                br.execution_time_ms
            FROM benchmark_results br
            JOIN benchmark_test_cases btc ON br.test_id = btc.test_id
            WHERE 1=1
        """
        params = []

        if category:
            query += " AND btc.test_category = %s"
            params.append(category)

        query += " ORDER BY br.execution_timestamp DESC LIMIT %s"
        params.append(limit_results)

        results = self.query(query, tuple(params) if params else None)

        if not results:
            return {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'success_rate': 0.0,
                'avg_execution_time_ms': 0,
                'category_breakdown': {}
            }

        # Calculate metrics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0

        # Calculate average execution time (only for tests with timing data)
        timed_results = [r['execution_time_ms'] for r in results if r['execution_time_ms'] is not None]
        avg_execution_time_ms = sum(timed_results) / len(timed_results) if timed_results else 0

        # Category breakdown
        category_breakdown = {}
        for result in results:
            cat = result['test_category']
            if cat not in category_breakdown:
                category_breakdown[cat] = {'total': 0, 'passed': 0}
            category_breakdown[cat]['total'] += 1
            if result['passed']:
                category_breakdown[cat]['passed'] += 1

        # Calculate success rate per category
        for cat in category_breakdown:
            total = category_breakdown[cat]['total']
            passed = category_breakdown[cat]['passed']
            category_breakdown[cat]['success_rate'] = (passed / total * 100) if total > 0 else 0.0

        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': round(success_rate, 2),
            'avg_execution_time_ms': round(avg_execution_time_ms, 2),
            'category_breakdown': category_breakdown
        }

    def getRecentBenchmarkResults(self, limit=20):
        """
        Get recent benchmark results with test case details.

        Args:
            limit: Number of recent results to retrieve (default 20)

        Returns:
            List of result dictionaries with test case details
        """
        query = """
            SELECT
                br.result_id,
                br.test_id,
                btc.test_name,
                btc.test_category,
                br.execution_timestamp,
                br.passed,
                br.execution_time_ms,
                br.error_message
            FROM benchmark_results br
            JOIN benchmark_test_cases btc ON br.test_id = btc.test_id
            ORDER BY br.execution_timestamp DESC
            LIMIT %s
        """

        return self.query(query, (limit,))

    def getLLMRoles(self) -> dict:
        """
        Retrieve all active LLM role configurations from database.

        Returns:
            dict: Dictionary containing role configurations for LLM client
        """
        query = """
            SELECT role_name, domain, specific_instructions,
                   background_context, few_shot_examples
            FROM llm_roles
            WHERE is_active = TRUE
            ORDER BY role_id
        """

        roles_data = self.query(query)

        # Convert to dictionary format expected by LLM client
        roles_dict = {}
        for role in roles_data:
            role_name = role['role_name']
            roles_dict[role_name] = {
                'role': role_name,
                'domain': role['domain'],
                'specific_instructions': role['specific_instructions'],
                'background_context': role['background_context'],
                'few_shot_examples': role['few_shot_examples']
            }

        return roles_dict






