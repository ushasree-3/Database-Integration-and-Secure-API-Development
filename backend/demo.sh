#!/bin/bash

# Sports Management API Demo Script

BASE_URL="http://localhost:5001" 

echo "==============================================="
echo "=== STEP 0: OBTAINING AUTH TOKENS ==="
echo "==============================================="
echo

# Function to extract token (handles potential errors slightly better)
extract_token() {
    RESPONSE=$1
    # TOKEN=$(echo "$RESPONSE" | grep -o '"session_token":\s*"[^"]' | grep -o '[^"]$' | tail -n 1)
    TOKEN=$(echo "$RESPONSE" | grep -o '"session_token": *"[^"]*"' | cut -d '"' -f4)

    if [ -z "$TOKEN" ]; then
        echo "ERROR: Could not extract token from response: $RESPONSE" >&2
        return 1
    fi
    echo "$TOKEN"
    return 0
}

# --- Get Tokens ---
echo "Logging in Admin (User 2209)..."
ADMIN_LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/login" -H "Content-Type: application/json" -d '{"user": "2209", "password": "default123"}')
ADMIN_TOKEN=$(extract_token "$ADMIN_LOGIN_RESPONSE")
if [ $? -ne 0 ]; then exit 1; fi
echo "Admin Token obtained (first 10 chars): ${ADMIN_TOKEN:0:10}..."
echo

echo "Logging in Coach (User 2210)..."
COACH_LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/login" -H "Content-Type: application/json" -d '{"user": "2210", "password": "default123"}')
COACH_TOKEN=$(extract_token "$COACH_LOGIN_RESPONSE")
if [ $? -ne 0 ]; then exit 1; fi
echo "Coach Token obtained (first 10 chars): ${COACH_TOKEN:0:10}..."
echo

echo "Logging in Organizer (User 2218)..."
ORGANIZER_LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/login" -H "Content-Type: application/json" -d '{"user": "2218", "password": "default123"}')
ORGANIZER_TOKEN=$(extract_token "$ORGANIZER_LOGIN_RESPONSE")
if [ $? -ne 0 ]; then exit 1; fi
echo "Organizer Token obtained (first 10 chars): ${ORGANIZER_TOKEN:0:10}..."
echo

echo "Logging in Referee (User 2214)..."
REFEREE_LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/login" -H "Content-Type: application/json" -d '{"user": "2214", "password": "default123"}')
REFEREE_TOKEN=$(extract_token "$REFEREE_LOGIN_RESPONSE")
if [ $? -ne 0 ]; then exit 1; fi
echo "Referee Token obtained (first 10 chars): ${REFEREE_TOKEN:0:10}..."
echo

echo "Logging in Equipment Manager (User 2215)..."
EQMAN_LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/login" -H "Content-Type: application/json" -d '{"user": "2215", "password": "default123"}')
EQMAN_TOKEN=$(extract_token "$EQMAN_LOGIN_RESPONSE")
if [ $? -ne 0 ]; then exit 1; fi
echo "EqManager Token obtained (first 10 chars): ${EQMAN_TOKEN:0:10}..."
echo

echo "Logging in Player (User 2216)..."
PLAYER_LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/login" -H "Content-Type: application/json" -d '{"user": "2216", "password": "default123"}')
PLAYER_TOKEN=$(extract_token "$PLAYER_LOGIN_RESPONSE")
if [ $? -ne 0 ]; then exit 1; fi
echo "Player Token obtained (first 10 chars): ${PLAYER_TOKEN:0:10}..."
echo "------------------------------------"

sleep 1

echo "==============================================="
echo "=== STEP 1: SETUP BY ORGANIZER & COACH ==="
echo "==============================================="
echo

# --- Organizer creates Venue ---
echo "Organizer (2218) creating Venue..."
VENUE_RESPONSE=$(curl -s -X POST "${BASE_URL}/venues/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $ORGANIZER_TOKEN" \
     -d '{"venue_name": "Demo Day Court", "location": "University Grounds"}')
echo "$VENUE_RESPONSE"
VENUE_ID=$(echo "$VENUE_RESPONSE" | grep -o '"VenueID":\s*[0-9]' | grep -o '[0-9]')
if [ -z "$VENUE_ID" ]; then echo "ERROR: Failed to create Venue"; exit 1; fi
echo ">> Venue created with ID: $VENUE_ID"
echo "------------------------------------"
sleep 1

# --- Organizer creates Event ---
echo "Organizer (2218) creating Event..."
EVENT_RESPONSE=$(curl -s -X POST "${BASE_URL}/events/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $ORGANIZER_TOKEN" \
     -d '{
           "event_name": "Demo Day Tournament",
           "start_date": "2025-06-01",
           "end_date": "2025-06-02",
           "location": "University Grounds",
           "description": "A demonstration event",
           "organizer_id": 2218
         }')
echo "$EVENT_RESPONSE"
EVENT_ID=$(echo "$EVENT_RESPONSE" | grep -o '"event_id":\s*[0-9]' | grep -o '[0-9]')
if [ -z "$EVENT_ID" ]; then echo "ERROR: Failed to create Event"; exit 1; fi
echo ">> Event created with ID: $EVENT_ID"
echo "------------------------------------"
sleep 1

# --- Coach creates Teams ---
echo "Coach (2210) creating Team A..."
TEAM_A_RESPONSE=$(curl -s -X POST "${BASE_URL}/teams/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN" \
     -d '{"team_name": "Demo Team Alpha ", "captain_id": 2221, "coach_id": 2210}')
echo "$TEAM_A_RESPONSE"
TEAM_ID_A=$(echo "$TEAM_A_RESPONSE" | grep -o '"TeamID":\s*[0-9]' | grep -o '[0-9]')
if [ -z "$TEAM_ID_A" ]; then echo "ERROR: Failed to create Team A"; exit 1; fi
echo ">> Team A created with ID: $TEAM_ID_A"
echo

echo "Coach (2220) creating Team B..." 
COACH_TOKEN_B=$(extract_token "$(curl -s -X POST ${BASE_URL}/login -H "Content-Type: application/json" -d '{"user": "2220", "password": "default123"}')")
if [ $? -ne 0 ]; then exit 1; fi
TEAM_B_RESPONSE=$(curl -s -X POST "${BASE_URL}/teams/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN_B" \
     -d '{"team_name": "Demo Team Beta", "captain_id": 2222, "coach_id": 2220}')
echo "$TEAM_B_RESPONSE"
TEAM_ID_B=$(echo "$TEAM_B_RESPONSE" | grep -o '"TeamID":\s*[0-9]' | grep -o '[0-9]')
if [ -z "$TEAM_ID_B" ]; then echo "ERROR: Failed to create Team B"; exit 1; fi
echo ">> Team B created with ID: $TEAM_ID_B"
echo "------------------------------------"
sleep 1

# --- Coaches add Players to Teams for the Event ---
echo "Coach (2210) adding players to Team A (ID: $TEAM_ID_A) for Event $EVENT_ID..."
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN" \
     -d '{"member_id": 2223, "position": "Hitter A1"}'
echo
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN" \
     -d '{"member_id": 2224, "position": "Blocker A2"}'
echo
# Add more players if needed for min count (assuming 6 needed)
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players" -H "Content-Type: application/json" -H "Authorization: Bearer $COACH_TOKEN" -d '{"member_id": 2225}'
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players" -H "Content-Type: application/json" -H "Authorization: Bearer $COACH_TOKEN" -d '{"member_id": 2229}'
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players" -H "Content-Type: application/json" -H "Authorization: Bearer $COACH_TOKEN" -d '{"member_id": 2230}'
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN" \
     -d '{"member_id": 2221, "position": "Captain A"}' # Add captain too
echo ">> Players added to Team A for Event $EVENT_ID."
echo

echo "Coach (2220) adding players to Team B (ID: $TEAM_ID_B) for Event $EVENT_ID..."
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players" -H "Content-Type: application/json" -H "Authorization: Bearer $COACH_TOKEN_B" -d '{"member_id": 2226}'
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players" -H "Content-Type: application/json" -H "Authorization: Bearer $COACH_TOKEN_B" -d '{"member_id": 2227}'
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players" -H "Content-Type: application/json" -H "Authorization: Bearer $COACH_TOKEN_B" -d '{"member_id": 2228}'
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players" -H "Content-Type: application/json" -H "Authorization: Bearer $COACH_TOKEN_B" -d '{"member_id": 2231}'
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players" -H "Content-Type: application/json" -H "Authorization: Bearer $COACH_TOKEN_B" -d '{"member_id": 2232}'
curl -s -X POST "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN_B" \
     -d '{"member_id": 2222, "position": "Captain B"}' # Add captain
echo ">> Players added to Team B for Event $EVENT_ID."
echo "------------------------------------"
sleep 1

# --- Coach Registers Team for Event ---
echo "Coach (2210) registering Team A (ID: $TEAM_ID_A) for Event $EVENT_ID..."
curl -s -X POST "${BASE_URL}/events/${EVENT_ID}/registrations" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN" \
     -d "{\"team_id\": ${TEAM_ID_A}}" # Note escaping for variable in JSON string
echo
echo "Coach (2220) registering Team B (ID: $TEAM_ID_B) for Event $EVENT_ID..."
curl -s -X POST "${BASE_URL}/events/${EVENT_ID}/registrations" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN_B" \
     -d "{\"team_id\": ${TEAM_ID_B}}"
echo ">> Teams registered for Event $EVENT_ID."
echo "------------------------------------"
sleep 1

# --- Equipment Manager adds Equipment ---
echo "EqManager (2215) adding Equipment..."
EQUIP_RESPONSE=$(curl -s -X POST "${BASE_URL}/equipment/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $EQMAN_TOKEN" \
     -d '{"equipment_name": "Demo Volleyball", "condition": "Good", "last_checked_date": "2025-04-15"}')
echo "$EQUIP_RESPONSE"
EQUIP_ID=$(echo "$EQUIP_RESPONSE" | grep -o '"EquipmentID":\s*[0-9]' | grep -o '[0-9]')
if [ -z "$EQUIP_ID" ]; then echo "ERROR: Failed to add Equipment"; exit 1; fi
echo ">> Equipment added with ID: $EQUIP_ID"
echo "------------------------------------"
sleep 1

echo "==============================================="
echo "=== STEP 2: SCHEDULING & OPERATIONS ==="
echo "==============================================="
echo

# --- Organizer Schedules Match ---
echo "Organizer (2218) scheduling match between Team A ($TEAM_ID_A) and Team B ($TEAM_ID_B) for Event $EVENT_ID at Venue $VENUE_ID..."
MATCH_RESPONSE=$(curl -s -X POST "${BASE_URL}/matches/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $ORGANIZER_TOKEN" \
     -d "{
           \"event_id\": ${EVENT_ID},
           \"team1_id\": ${TEAM_ID_A},
           \"team2_id\": ${TEAM_ID_B},
           \"match_date\": \"2025-06-01\",
           \"slot\": \"09:30-11:00\",
           \"venue_id\": ${VENUE_ID}
         }")
echo "$MATCH_RESPONSE"
MATCH_ID=$(echo "$MATCH_RESPONSE" | grep -o '"MatchID":\s*[0-9]' | grep -o '[0-9]')
if [ -z "$MATCH_ID" ]; then echo "ERROR: Failed to schedule Match"; exit 1; fi
echo ">> Match scheduled with ID: $MATCH_ID"
echo "------------------------------------"
sleep 1

# --- Player views Team List ---
echo "Player (2223) views list of teams..."
curl -s -X GET "${BASE_URL}/teams/" \
     -H "Authorization: Bearer $PLAYER_TOKEN"
echo; echo "------------------------------------"
sleep 1

# --- Coach Borrows Equipment ---
echo "Coach (2210) borrows Equipment ID: $EQUIP_ID for Member 2210..."
LOG_RESPONSE=$(curl -s -X POST "${BASE_URL}/equipment/logs/borrow" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN" \
     -d "{\"equipment_id\": ${EQUIP_ID}, \"issued_to\": 2210}")
echo "$LOG_RESPONSE"
LOG_ID=$(echo "$LOG_RESPONSE" | grep -o '"LogID":\s*[0-9]' | grep -o '[0-9]')
if [ -z "$LOG_ID" ]; then echo "ERROR: Failed to borrow equipment"; exit 1; fi
echo ">> Equipment borrowed, Log ID: $LOG_ID"
echo "------------------------------------"
sleep 1

# --- Referee Updates Match Result ---
echo "Referee (3120) updates result for Match ID: $MATCH_ID..."
curl -s -X PUT "${BASE_URL}/matches/${MATCH_ID}/score" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $REFEREE_TOKEN" \
     -d "{
           \"team1_score\": 3,
           \"team2_score\": 1,
           \"winner_id\": ${TEAM_ID_A}
         }"
echo; echo "------------------------------------"
sleep 1

# --- Coach Updates Player Performance ---
echo "Coach (2210) updates performance for Player 2223 in Team ${TEAM_ID_A}/Event ${EVENT_ID}..."
# Check if PlayerID exists for this combo first
# Need to know the PlayerID generated when 2223 was added to Team A / Event 1
# Let's assume it was PlayerID 2 based on sample data logic
PLAYER_RECORD_ID_2223=2 # ** ADJUST THIS if needed based on actual DB data **
curl -s -X PUT "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players/${PLAYER_RECORD_ID_2223}/performance" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN" \
     -d '{"performance_statistics": 0.88}'
echo; echo "------------------------------------"
sleep 1

# --- Admin Updates Event Description ---
echo "Admin (2209) updates Event $EVENT_ID description..."
curl -s -X PUT "${BASE_URL}/events/${EVENT_ID}" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d '{"description": "Updated description: Annual demonstration tournament."}'
echo; echo "------------------------------------"
sleep 1

# --- Player Returns Equipment ---
echo "Player (2210 - assuming they return it) returns Equipment via Log ID: $LOG_ID..."
# Need a token for user 2210 (Coach token can work here based on RBAC)
curl -s -X PUT "${BASE_URL}/equipment/logs/${LOG_ID}/return" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $COACH_TOKEN" \
     -d '{"condition": "Good"}' # Optional: Update condition on return
echo; echo "------------------------------------"
sleep 1


echo "==============================================="
echo "=== STEP 3: CLEANUP (DELETE CREATED ITEMS) ==="
echo "==============================================="
echo "*NOTE: Deletions must succeed in order. If dependencies exist (e.g., players still on team when deleting team), deletion will fail.*"
echo

# --- Delete Match Result (No specific endpoint, just delete Match) ---

# --- Delete Match ---
echo "Admin deleting Match ID: $MATCH_ID..."
curl -s -X DELETE "${BASE_URL}/matches/${MATCH_ID}" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
echo; echo "------------------------------------"
sleep 1

# --- Unregister Teams ---
echo "Admin unregistering Team A (ID: $TEAM_ID_A) from Event $EVENT_ID..."
curl -s -X DELETE "${BASE_URL}/events/${EVENT_ID}/registrations/${TEAM_ID_A}" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
echo
echo "Admin unregistering Team B (ID: $TEAM_ID_B) from Event $EVENT_ID..."
curl -s -X DELETE "${BASE_URL}/events/${EVENT_ID}/registrations/${TEAM_ID_B}" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
echo; echo "------------------------------------"
sleep 1

# --- Remove Players from Teams/Event ---
echo "Admin removing players from Team A (ID: $TEAM_ID_A) for Event $EVENT_ID..."
# Need the MemberIDs used: 2223, 2224, 2225, 2229, 2230, 2221
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players/2223" -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players/2224" -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players/2225" -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players/2229" -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players/2230" -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_A}/events/${EVENT_ID}/players/2221" -H "Authorization: Bearer $ADMIN_TOKEN"
echo

echo "Admin removing players from Team B (ID: $TEAM_ID_B) for Event $EVENT_ID..."
# Need the MemberIDs used: 2226, 2227, 2228, 2231, 2232, 2222
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players/2226" -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players/2227" -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players/2228" -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players/2231" -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players/2232" -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_B}/events/${EVENT_ID}/players/2222" -H "Authorization: Bearer $ADMIN_TOKEN"
echo ">> Players removed from teams for Event $EVENT_ID."
echo "------------------------------------"
sleep 1

# --- Delete Event ---
echo "Admin deleting Event ID: $EVENT_ID..."
curl -s -X DELETE "${BASE_URL}/events/${EVENT_ID}" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
echo; echo "------------------------------------"
sleep 1

# --- Delete Teams ---
echo "Admin deleting Team A (ID: $TEAM_ID_A)..."
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_A}" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
echo
echo "Admin deleting Team B (ID: $TEAM_ID_B)..."
curl -s -X DELETE "${BASE_URL}/teams/${TEAM_ID_B}" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
echo; echo "------------------------------------"
sleep 1

# --- Delete Venue ---
echo "Admin deleting Venue ID: $VENUE_ID..."
curl -s -X DELETE "${BASE_URL}/venues/${VENUE_ID}" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
echo; echo "------------------------------------"
sleep 1

# --- Delete Equipment Log (No specific endpoint, usually kept for history) ---
echo "(Skipping specific EquipmentLog deletion)"

# --- Delete Equipment ---
echo "Admin deleting Equipment ID: $EQUIP_ID..."
curl -s -X DELETE "${BASE_URL}/equipment/${EQUIP_ID}" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
echo; echo "------------------------------------"

echo "=== DEMO COMPLETE ==="