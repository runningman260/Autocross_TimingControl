# Sandbox for testing Python Code

## Database Trigger Testing

1. Create a test database
2. In the database environment itself:

	a.  set up the trigger to kick off a function for each row entry

	```console
	create or replace trigger notify_trigger
	after insert or update on "run_order"
	for each row execute function notify_trigger_function();
	```

	b.  set up the function which will notify any listeners of the action

	```console
	create or replace function notify_trigger_function() 
	returns trigger as $$
	begin 
    	perform pg_notify('new_id', row_to_json(new)::text);
    	return new; 
	end; 
	$$ language plpgsql;
	```

3. Start the python db_listener script.
4. Start the Insert test script. New rows should be shown in both scripts' standard output if the trigger is working.