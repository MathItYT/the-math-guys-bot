from discord import Guild, Member
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
        if str(member.id) not in bounties or bounties[str(member.id)] == 0:
            print(f"Setting up {member}")
            bounties[str(member.id)] = 50
    
    with open("bounties.json", "w") as f:
        json.dump(bounties, f)


def add_points(username: Member, points_to_add: int):
    if not os.path.exists("bounties.json"):
        raise FileNotFoundError("bounties.json not found. Please run setup_users(guild) first.")
    with open("bounties.json", "r") as f:
        bounties = json.load(f)

    if str(username.id) not in bounties:
        raise ValueError(f"User {username} not found in bounties.json. Please run setup_users(guild) first.")
    bounties[str(username.id)] += points_to_add
    bounties[str(username.id)] = max(0, bounties[str(username.id)])

    with open("bounties.json", "w") as f:
        json.dump(bounties, f)


def get_points(user: Member) -> int:
    with open("bounties.json", "r") as f:
        bounties = json.load(f)
    if str(user.id) not in bounties:
        raise ValueError(f"User with id {user.id} not found in bounties.json. Please run setup_users(guild) first.")
    return bounties[str(user.id)]


async def get_leaderboard(guild: Guild) -> list[tuple[str, int]]:
    with open("bounties.json", "r") as f:
        bounties = json.load(f)

    items = list(sorted(bounties.items(), key=lambda x: x[1], reverse=True))
    # Convert user ids to usernames
    new_items = []
    for user, points in items:
        try:
            member = await guild.fetch_member(user)
        except:
            continue
        new_items.append((member.name, points))
    return new_items[:10]


def subtract_points(username: Member, points_to_subtract: int):
    add_points(username, -points_to_subtract)


def exchange_points(username1: Member, username2: Member, points: int):
    add_points(username1, points)
    subtract_points(username2, points)
