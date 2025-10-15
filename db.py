# import sqlite3

    
# delete_team_memberships = """
# DELETE FROM team_members"""
# delete_projects = """DELETE FROM projects"""

# def delete_team_memberships_db(conn: sqlite3.Connection):
#     with conn:
#         conn.execute(delete_team_memberships)
#         conn.execute(delete_projects)
#         conn.commit()
#         print("Deleted team memberships and projects successfully.")

# if __name__ == "__main__":
#     conn = sqlite3.connect('database/site.db')  # Replace with your database file
#     delete_team_memberships_db(conn)