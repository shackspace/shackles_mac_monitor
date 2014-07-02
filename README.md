# Shackles MAC Monitor

monitors joins/leaves in the shack network and sends status to shackles
adding your MAC address to shackles is opt-in, nothing will be saved forever.

users may have multiple mac addresses registered for their account, login
always superseeds a logout (e.g. you can have one of your devices being shut
down and still keep being online)

# install
add to your crontab:

    */5 * * * * python3 /opt/shackles_mac_monitor/read_mac.py
