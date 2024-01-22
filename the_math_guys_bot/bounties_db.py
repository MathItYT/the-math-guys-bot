from dotenv import load_dotenv
from discord import Client

# Load environment variables from the .env file
load_dotenv()
import os
import MySQLdb


def setup_users(client: Client):
    the_math_guys = client.get_guild(1045453708642758657)
    connection = MySQLdb.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USERNAME"),
        passwd=os.getenv("DATABASE_PASSWORD"),
        db=os.getenv("DATABASE"),
        autocommit=True,
        ssl_mode="VERIFY_IDENTITY",
        # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
        # to determine the path to your operating systems certificate file.
    )

    try:
        # Create a cursor to interact with the database
        cursor = connection.cursor()

        # Create database if it doesn't exist
        cursor.execute("""CREATE TABLE IF NOT EXISTS bounties(
        username VARCHAR(255) NOT NULL,
        points INT UNSIGNED NOT NULL
        PRIMARY KEY (username)
    )"""
        )

        # Adds all users to the database
        for member in the_math_guys.members:
            cursor.execute(f"INSERT IGNORE INTO bounties (username, points) VALUES ('{member}', 10)")
        
        # Commit the changes
        connection.commit()

    except MySQLdb.Error as e:
        print("MySQL Error:", e)

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()


def add_points(username: str, points_to_add: int):
    connection = MySQLdb.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USERNAME"),
        passwd=os.getenv("DATABASE_PASSWORD"),
        db=os.getenv("DATABASE"),
        autocommit=True,
        ssl_mode="VERIFY_IDENTITY",
        # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
        # to determine the path to your operating systems certificate file.
    )

    try:
        # Create a cursor to interact with the database
        cursor = connection.cursor()

        # Get the points of the user
        points = get_points(username)

        # Set the points of the user
        cursor.execute(f"UPDATE bounties SET points = {points + points_to_add} WHERE username = '{username}'")
        # Commit the changes
        connection.commit()

    except MySQLdb.Error as e:
        print("MySQL Error:", e)

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()


def subtract_points(username: str, points_to_subtract: int):
    connection = MySQLdb.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USERNAME"),
        passwd=os.getenv("DATABASE_PASSWORD"),
        db=os.getenv("DATABASE"),
        autocommit=True,
        ssl_mode="VERIFY_IDENTITY",
        # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
        # to determine the path to your operating systems certificate file.
    )

    try:
        # Create a cursor to interact with the database
        cursor = connection.cursor()

        # Get the points of the user
        points = get_points(username)

        # Set the points of the user
        cursor.execute(f"UPDATE bounties SET points = {max(0, points - points_to_subtract)} WHERE username = '{username}'")
        # Commit the changes
        connection.commit()

    except MySQLdb.Error as e:
        print("MySQL Error:", e)

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()


def get_points(username: str) -> int:
    connection = MySQLdb.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USERNAME"),
        passwd=os.getenv("DATABASE_PASSWORD"),
        db=os.getenv("DATABASE"),
        autocommit=True,
        ssl_mode="VERIFY_IDENTITY",
        # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
        # to determine the path to your operating systems certificate file.
    )

    try:
        # Create a cursor to interact with the database
        cursor = connection.cursor()

        # Get the points of the user
        cursor.execute(f"SELECT points FROM bounties WHERE username = '{username}'")
        points = cursor.fetchone()[0]

        return points

    except MySQLdb.Error as e:
        print("MySQL Error:", e)

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()


def get_leaderboard() -> list[tuple[str, int]]:
    connection = MySQLdb.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USERNAME"),
        passwd=os.getenv("DATABASE_PASSWORD"),
        db=os.getenv("DATABASE"),
        autocommit=True,
        ssl_mode="VERIFY_IDENTITY",
        # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
        # to determine the path to your operating systems certificate file.
    )

    try:
        # Create a cursor to interact with the database
        cursor = connection.cursor()

        # Get the points of the user
        cursor.execute(f"SELECT username, points FROM bounties ORDER BY points DESC")
        leaderboard = cursor.fetchall()

        return leaderboard

    except MySQLdb.Error as e:
        print("MySQL Error:", e)

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()


def get_rank(username: str) -> int:
    connection = MySQLdb.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USERNAME"),
        passwd=os.getenv("DATABASE_PASSWORD"),
        db=os.getenv("DATABASE"),
        autocommit=True,
        ssl_mode="VERIFY_IDENTITY",
        # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
        # to determine the path to your operating systems certificate file.
    )

    try:
        # Create a cursor to interact with the database
        cursor = connection.cursor()

        # Get the points of the user
        cursor.execute(f"SELECT COUNT(*) FROM bounties WHERE points > (SELECT points FROM bounties WHERE username = '{username}')")
        rank = cursor.fetchone()[0] + 1

        return rank

    except MySQLdb.Error as e:
        print("MySQL Error:", e)

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()


def exchange_points(username1: str, username2: str, points: int):
    connection = MySQLdb.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USERNAME"),
        passwd=os.getenv("DATABASE_PASSWORD"),
        db=os.getenv("DATABASE"),
        autocommit=True,
        ssl_mode="VERIFY_IDENTITY",
        # See https://planetscale.com/docs/concepts/secure-connections#ca-root-configuration
        # to determine the path to your operating systems certificate file.
    )

    try:
        # Create a cursor to interact with the database
        cursor = connection.cursor()

        # Add points to user 1
        add_points(username1, points)

        # Subtract points from user 2
        subtract_points(username2, points)

    except MySQLdb.Error as e:
        print("MySQL Error:", e)
    
    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()
