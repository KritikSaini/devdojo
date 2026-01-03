# import os
# import boto3
# from dotenv import load_dotenv
# from datetime import datetime, timedelta

# load_dotenv()

# # Initialize the Boto3 SNS client using credentials from environment variables
# sns = boto3.client(
#     "sns",
#     region_name=os.getenv("AWS_REGION"),
#     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
# )

# SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")


# # ✅ Check if email is already subscribed
# def is_email_subscribed(email: str) -> bool:
#     try:
#         response = sns.list_subscriptions_by_topic(TopicArn=SNS_TOPIC_ARN)
#         for sub in response.get("Subscriptions", []):
#             if sub["Protocol"] == "email" and sub["Endpoint"] == email:
#                 return True
#         return False
#     except Exception as e:
#         print(f"[SNS ERROR] Failed to check subscriptions: {e}")
#         return False


# # ✅ Subscribe user to SNS topic
# def subscribe_user_to_topic(email: str):
#     if not SNS_TOPIC_ARN:
#         print("[SNS ERROR] SNS_TOPIC_ARN is not configured in .env file.")
#         return None
#     try:
#         print(f"[SNS] Subscribing {email} to SNS topic...")
#         response = sns.subscribe(
#             TopicArn=SNS_TOPIC_ARN,
#             Protocol="email",
#             Endpoint=email,
#             ReturnSubscriptionArn=False  # They need to confirm manually
#         )
#         print(f"[SNS] Subscription request sent to {email}")
#         return response
#     except Exception as e:
#         print(f"[SNS ERROR] Could not subscribe {email}: {e}")
#         return None


# # 🔔 Called when a user joins a group
# def notify_user_joined_group(email: str, group_name: str):
#     """
#     Sends a notification when a user joins a group.
#     First subscribes the user if needed.
#     """
#     if not SNS_TOPIC_ARN:
#         print("[SNS ERROR] SNS_TOPIC_ARN is not configured in .env file.")
#         return None

#     # Step 1: Subscribe user to SNS if not already subscribed
#     if not is_email_subscribed(email):
#         subscribe_user_to_topic(email)
#         print(f"[SNS] Waiting for {email} to confirm subscription before sending messages.")
#         return None  # Wait for confirmation before publishing

#     # Step 2: Send actual group join message
#     subject = f"You joined the group '{group_name}'"
#     message = f"""
# Hello!

# You have successfully joined the group: '{group_name}'.

# Stay tuned for upcoming challenges and discussions in your group.

# Welcome aboard!

# - The Dojo Team
# """

#     try:
#         print(f"[SNS] Sending group join notification to topic for user {email}")
#         response = sns.publish(
#             TopicArn=SNS_TOPIC_ARN,
#             Subject=subject,
#             Message=message
#         )
#         print(f"[SNS Success] Sent group join notification for {email}.")
#         return response
#     except Exception as e:
#         print(f"[SNS ERROR] Could not send group join notification: {e}")
#         return None


# # 🔔 Challenge repo notification
# def notify_member_of_new_repo(
#     email: str,
#     challenge_title: str,
#     repo_name: str,
#     clone_url: str | None
# ):
#     """
#     Sends a personalized email to a single user about their challenge.
#     The message content changes based on whether the repo was created successfully.
#     """
#     if not SNS_TOPIC_ARN:
#         print("[SNS ERROR] SNS_TOPIC_ARN is not configured in .env file.")
#         return None

#     deadline = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M UTC')
#     subject = f"Your Personal Challenge Environment for '{challenge_title}'"

#     if clone_url:
#         repo_section = f"""
# Your personal, private repository for this challenge has been created.

# Repo Name: {repo_name}
# Clone URL: {clone_url}

# Please accept the collaborator invitation you receive from GitHub to gain push access.
# """
#     else:
#         repo_section = f"""
# There was an issue creating your personal GitHub repository for this challenge. Please contact an administrator for assistance. You can still view the challenge details on the platform.
# """

#     message = f"""
# Hello!

# A new challenge, '{challenge_title}', has started in your group.

# {repo_section}

# **Deadline:** You have 8 hours to submit your solution. The deadline is {deadline}.

# Good luck!

# - The Dojo Team
# """

#     try:
#         print(f"[SNS] Sending personalized repo notification to topic for user {email}")
#         response = sns.publish(
#             TopicArn=SNS_TOPIC_ARN,
#             Subject=subject,
#             Message=message
#         )
#         print(f"[SNS Success] Sent notification regarding repo {repo_name}.")
#         return response
#     except Exception as e:
#         print(f"[SNS ERROR] Could not send personalized notification: {e}")
#         return None

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")


# 🔧 Helper: create SNS client ONLY when needed
def get_sns_client():
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    # 🚫 Disable SNS if not configured (Render-safe)
    if not AWS_REGION or not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        print("SNS disabled: AWS credentials not configured")
        return None

    import boto3  # ✅ import inside function

    return boto3.client(
        "sns",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


# ✅ Check if email is already subscribed
def is_email_subscribed(email: str) -> bool:
    sns = get_sns_client()
    if not sns or not SNS_TOPIC_ARN:
        return False

    try:
        response = sns.list_subscriptions_by_topic(TopicArn=SNS_TOPIC_ARN)
        for sub in response.get("Subscriptions", []):
            if sub["Protocol"] == "email" and sub["Endpoint"] == email:
                return True
        return False
    except Exception as e:
        print(f"[SNS ERROR] Failed to check subscriptions: {e}")
        return False


# ✅ Subscribe user to SNS topic
def subscribe_user_to_topic(email: str):
    sns = get_sns_client()
    if not sns or not SNS_TOPIC_ARN:
        return None

    try:
        return sns.subscribe(
            TopicArn=SNS_TOPIC_ARN,
            Protocol="email",
            Endpoint=email,
            ReturnSubscriptionArn=False
        )
    except Exception as e:
        print(f"[SNS ERROR] Could not subscribe {email}: {e}")
        return None


# 🔔 User joined group
def notify_user_joined_group(email: str, group_name: str):
    sns = get_sns_client()
    if not sns or not SNS_TOPIC_ARN:
        return None

    if not is_email_subscribed(email):
        subscribe_user_to_topic(email)
        return None

    subject = f"You joined the group '{group_name}'"
    message = f"""
Hello!

You have successfully joined the group: '{group_name}'.

Welcome aboard!
- The Dojo Team
"""

    try:
        return sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        print(f"[SNS ERROR] Could not send group join notification: {e}")
        return None


# 🔔 Challenge repo notification
def notify_member_of_new_repo(
    email: str,
    challenge_title: str,
    repo_name: str,
    clone_url: str | None
):
    sns = get_sns_client()
    if not sns or not SNS_TOPIC_ARN:
        return None

    deadline = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M UTC')
    subject = f"Your Personal Challenge Environment for '{challenge_title}'"

    message = f"""
Hello!

A new challenge '{challenge_title}' has started.

Repo: {repo_name}
Clone URL: {clone_url or "Not created"}

Deadline: {deadline}

- The Dojo Team
"""

    try:
        return sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        print(f"[SNS ERROR] Could not send repo notification: {e}")
        return None





