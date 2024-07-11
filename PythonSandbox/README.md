# Sandbox for testing Python Code

## Database Trigger Testing

1. In the database environment itself:

	a.  set up the trigger to kick off a function for each row entry
	
	b.  set up the function which will notify any listeners of the action

2. Start the python db_listener script.

3. Start the Insert test script. New rows should be shown in both scripts' standard output if the trigger is working.