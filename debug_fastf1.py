import fastf1

try:
    session = fastf1.get_session(2023, 1, 'R')
    print("Session Event Type:", type(session.event))
    print("Session Event Keys/Attributes:")
    print(session.event)
    try:
        print("Test .Year:", session.event.Year)
    except Exception as e:
        print("Error accessing .Year:", e)
        
    try:
        print("Test ['Year']:", session.event['Year'])
    except Exception as e:
        print("Error accessing ['Year']:", e)

except Exception as e:
    print(f"Global Error: {e}")
