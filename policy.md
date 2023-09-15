```markdown
# Why we collect and use data

Collecting data is necessary in order to make the bot run properly.
Without storing some aspects of your user data, the bot would not be able to run.

# What data is collected

We collect the following:

* User IDs

    Required for functionality of the blacklist command.

* Guild/Channel ID pairs

    Required for the functionality of the announcements and announcements command.

* Messages

    Messages are not stored, but they are used for the main functionality of cheeseBot.
    A message gets checked, if it has a keyword that's in the list of possible cheese words,
    it will react and send a DM, then it will move on to check the next message sent.
    Users can opt-out of this feature by using the blacklist command.

# Where data is stored and secured

Data that we collect is stored in a database. This database is not accessible by other entities.
The server that the database is kept on is stored in the US.

# Where data is shared

Raw data is not shared with other entities. 

# Concerns

If you have any concerns about the usage of your data, please contact us.
```
