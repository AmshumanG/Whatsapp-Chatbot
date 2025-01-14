import pywhatkit
from datetime import datetime

# Get the current time
now = datetime.now()

# Get the current hour in 24-hour format
chour = now.strftime("%H")

# Prompt the user to enter the phone number
mobile = input('Enter Mobile No of Receiver: ')

# Add a default country code if not provided (example: +1 for the USA)
if not mobile.startswith('+91'):
    mobile = '+91' + mobile  # Replace +1 with your default country code

# Prompt the user to enter the message
message = input('Enter Message you wanna send: ')

# Prompt the user to enter the hour and minute
hour = int(input('Enter hour (24-hour format): '))
minute = int(input('Enter minute: '))

# Send the message using pywhatkit
pywhatkit.sendwhatmsg(mobile, message, hour, minute)
