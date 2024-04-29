from discord import Guild
import json
import os


def setup_users(guild: Guild):
    if os.path.exists("bounties.json"):
        with open("bounties.json", "r") as f:
            bounties = json.load(f)
    else:
        bounties = {}
    
    for member in guild.members:
        if member.bot:
            continue
        if member.id not in bounties:
            bounties[member.id] = 0
    
    with open("bounties.json", "w") as f:
        json.dump(bounties, f)


def add_points(username: str, points_to_add: int):
    if not os.path.exists("bounties.json"):
        raise FileNotFoundError("bounties.json not found. Please run setup_users(guild) first.")
    with open("bounties.json", "r") as f:
        bounties = json.load(f)

    if username not in bounties:
        raise ValueError(f"User {username} not found in bounties.json. Please run setup_users(guild) first.")
    bounties[username] += points_to_add
    bounties[username] = max(0, bounties[username])

    with open("bounties.json", "w") as f:
        json.dump(bounties, f)


def get_points(username: str) -> int:
    with open("bounties.json", "r") as f:
        bounties = json.load(f)

    if username not in bounties:
        raise ValueError(f"User {username} not found in bounties.json. Please run setup_users(guild) first.")
    return bounties[username]


def get_leaderboard() -> list[tuple[str, int]]:
    with open("bounties.json", "r") as f:
        bounties = json.load(f)

    return list(sorted(bounties.items(), key=lambda x: x[1], reverse=True))


def get_rank(username: str) -> int:
    leaderboard = get_leaderboard()
    for i, (user, _) in enumerate(leaderboard):
        if user == username:
            return i + 1
    return -1


def subtract_points(username: str, points_to_subtract: int):
    add_points(username, -points_to_subtract)


def exchange_points(username1: str, username2: str, points: int):
    add_points(username1, points)
    subtract_points(username2, points)
