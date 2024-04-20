from dotenv import load_dotenv
from discord import Guild

# Load environment variables from the .env file
load_dotenv()
import os
import pymysql
import sqlalchemy
from google.cloud.sql.connector import Connector


def init_connection_pool(connector: Connector) -> sqlalchemy.engine.Engine:
    # function used to generate database connection
    def getconn() -> pymysql.connections.Connection:
        conn = connector.connect(
            os.getenv("CONNECTION_NAME"),
            "pymysql",
            user=os.getenv("DATABASE_USERNAME"),
            password=os.getenv("DATABASE_PASSWORD"),
            db=os.getenv("DATABASE"),
        )
        return conn

    # create connection pool
    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
    )
    return pool


def setup_users(guild: Guild):
    with Connector() as connector:
        connection = init_connection_pool(connector)

        try:
            # Create a cursor to interact with the database
            with connection.connect() as conn:
                # Create database if it doesn't exist
                conn.execute("""CREATE TABLE IF NOT EXISTS bounties(
                username VARCHAR(255) NOT NULL,
                points INT UNSIGNED NOT NULL,
                PRIMARY KEY (username)
            )"""
                )

                # Adds all users to the database
                for member in guild.members:
                    conn.execute(f"INSERT IGNORE INTO bounties (username, points) VALUES ('{member}', 10)")

        except pymysql.Error as e:
            print("MySQL Error:", e)
        
        finally:
            connection.dispose()


def add_points(username: str, points_to_add: int):
#     connection = MySQLdb.connect(
#         host=os.getenv("DATABASE_HOST"),
#         user=os.getenv("DATABASE_USERNAME"),
#         passwd=os.getenv("DATABASE_PASSWORD"),
#         db=os.getenv("DATABASE"),
#         autocommit=True,
#         ssl_mode="VERIFY_IDENTITY",
#         # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
#         # to determine the path to your operating systems certificate file.
#     )

#     try:
#         # Create a cursor to interact with the database
#         cursor = connection.cursor()

#         # Get the points of the user
#         points = get_points(username)

#         # Set the points of the user
#         cursor.execute(f"UPDATE bounties SET points = {points + points_to_add} WHERE username = '{username}'")
#         # Commit the changes
#         connection.commit()

#     except MySQLdb.Error as e:
#         print("MySQL Error:", e)

#     finally:
#         # Close the cursor and connection
#         cursor.close()
#         connection.close()


# def subtract_points(username: str, points_to_subtract: int):
#     connection = MySQLdb.connect(
#         host=os.getenv("DATABASE_HOST"),
#         user=os.getenv("DATABASE_USERNAME"),
#         passwd=os.getenv("DATABASE_PASSWORD"),
#         db=os.getenv("DATABASE"),
#         autocommit=True,
#         ssl_mode="VERIFY_IDENTITY",
#         # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
#         # to determine the path to your operating systems certificate file.
#     )

#     try:
#         # Create a cursor to interact with the database
#         cursor = connection.cursor()

#         # Get the points of the user
#         points = get_points(username)

#         # Set the points of the user
#         cursor.execute(f"UPDATE bounties SET points = {max(0, points - points_to_subtract)} WHERE username = '{username}'")
#         # Commit the changes
#         connection.commit()

#     except MySQLdb.Error as e:
#         print("MySQL Error:", e)

#     finally:
#         # Close the cursor and connection
#         cursor.close()
#         connection.close()
    with Connector() as connector:
        connection = init_connection_pool(connector)

        try:
            # Create a cursor to interact with the database
            with connection.connect() as conn:
                # Get the points of the user
                points = get_points(username)

                # Set the points of the user
                conn.execute(f"UPDATE bounties SET points = {points + points_to_add} WHERE username = '{username}'")

        except pymysql.Error as e:
            print("MySQL Error:", e)
        
        finally:
            connection.dispose()


def get_points(username: str) -> int:
    # connection = MySQLdb.connect(
    #     host=os.getenv("DATABASE_HOST"),
    #     user=os.getenv("DATABASE_USERNAME"),
    #     passwd=os.getenv("DATABASE_PASSWORD"),
    #     db=os.getenv("DATABASE"),
    #     autocommit=True,
    #     ssl_mode="VERIFY_IDENTITY",
    #     # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
    #     # to determine the path to your operating systems certificate file.
    # )

    # try:
    #     # Create a cursor to interact with the database
    #     cursor = connection.cursor()

    #     # Get the points of the user
    #     cursor.execute(f"SELECT points FROM bounties WHERE username = '{username}'")
    #     points = cursor.fetchone()[0]

    #     return points

    # except MySQLdb.Error as e:
    #     print("MySQL Error:", e)

    # finally:
    #     # Close the cursor and connection
    #     cursor.close()
    #     connection.close()
    with Connector() as connector:
        connection = init_connection_pool(connector)

        try:
            # Create a cursor to interact with the database
            with connection.connect() as conn:
                # Get the points of the user
                points = conn.execute(f"SELECT points FROM bounties WHERE username = '{username}'").fetchone()[0]

                return points

        except pymysql.Error as e:
            print("MySQL Error:", e)
        
        finally:
            connection.dispose()


def get_leaderboard() -> list[tuple[str, int]]:
    # connection = MySQLdb.connect(
    #     host=os.getenv("DATABASE_HOST"),
    #     user=os.getenv("DATABASE_USERNAME"),
    #     passwd=os.getenv("DATABASE_PASSWORD"),
    #     db=os.getenv("DATABASE"),
    #     autocommit=True,
    #     ssl_mode="VERIFY_IDENTITY",
    #     # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
    #     # to determine the path to your operating systems certificate file.
    # )

    # try:
    #     # Create a cursor to interact with the database
    #     cursor = connection.cursor()

    #     # Get the points of the user
    #     cursor.execute(f"SELECT username, points FROM bounties ORDER BY points DESC")
    #     leaderboard = cursor.fetchall()

    #     return leaderboard

    # except MySQLdb.Error as e:
    #     print("MySQL Error:", e)

    # finally:
    #     # Close the cursor and connection
    #     cursor.close()
    #     connection.close()
    with Connector() as connector:
        connection = init_connection_pool(connector)

        try:
            # Create a cursor to interact with the database
            with connection.connect() as conn:
                # Get the points of the user
                leaderboard = conn.execute(f"SELECT username, points FROM bounties ORDER BY points DESC").fetchall()

                return leaderboard

        except pymysql.Error as e:
            print("MySQL Error:", e)
        
        finally:
            connection.dispose()


def get_rank(username: str) -> int:
    # connection = MySQLdb.connect(
    #     host=os.getenv("DATABASE_HOST"),
    #     user=os.getenv("DATABASE_USERNAME"),
    #     passwd=os.getenv("DATABASE_PASSWORD"),
    #     db=os.getenv("DATABASE"),
    #     autocommit=True,
    #     ssl_mode="VERIFY_IDENTITY",
    #     # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
    #     # to determine the path to your operating systems certificate file.
    # )

    # try:
    #     # Create a cursor to interact with the database
    #     cursor = connection.cursor()

    #     # Get the points of the user
    #     cursor.execute(f"SELECT COUNT(*) FROM bounties WHERE points > (SELECT points FROM bounties WHERE username = '{username}')")
    #     rank = cursor.fetchone()[0] + 1

    #     return rank

    # except MySQLdb.Error as e:
    #     print("MySQL Error:", e)

    # finally:
    #     # Close the cursor and connection
    #     cursor.close()
    #     connection.close()
    with Connector() as connector:
        connection = init_connection_pool(connector)

        try:
            # Create a cursor to interact with the database
            with connection.connect() as conn:
                # Get the points of the user
                rank = conn.execute(f"SELECT COUNT(*) FROM bounties WHERE points > (SELECT points FROM bounties WHERE username = '{username}')").fetchone()[0] + 1

                return rank

        except pymysql.Error as e:
            print("MySQL Error:", e)
        
        finally:
            connection.dispose()


def subtract_points(username: str, points_to_subtract: int):
    with Connector() as connector:
        connection = init_connection_pool(connector)

        try:
            # Create a cursor to interact with the database
            with connection.connect() as conn:
                # Get the points of the user
                points = get_points(username)

                # Set the points of the user
                conn.execute(f"UPDATE bounties SET points = {max(0, points - points_to_subtract)} WHERE username = '{username}'")

        except pymysql.Error as e:
            print("MySQL Error:", e)
        
        finally:
            connection.dispose()


def exchange_points(username1: str, username2: str, points: int):
    # connection = MySQLdb.connect(
    #     host=os.getenv("DATABASE_HOST"),
    #     user=os.getenv("DATABASE_USERNAME"),
    #     passwd=os.getenv("DATABASE_PASSWORD"),
    #     db=os.getenv("DATABASE"),
    #     autocommit=True,
    #     ssl_mode="VERIFY_IDENTITY",
    #     # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
    #     # to determine the path to your operating systems certificate file.
    # )

    # try:
    #     # Create a cursor to interact with the database
    #     cursor = connection.cursor()

    #     # Add points to user 1
    #     add_points(username1, points)

    #     # Subtract points from user 2
    #     subtract_points(username2, points)

    # except MySQLdb.Error as e:
    #     print("MySQL Error:", e)
    
    # finally:
    #     # Close the cursor and connection
    #     cursor.close()
    #     connection.close()
    add_points(username1, points)
    subtract_points(username2, points)
