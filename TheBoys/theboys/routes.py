from theboys import app, db, socketio
from flask import render_template, url_for, redirect, request, flash, session, get_flashed_messages, jsonify
from theboys.models import Users, ChatsSaved, ActiveLobby
import random
from string import ascii_uppercase
from flask_socketio import join_room, leave_room, send

def generateRandomCode():
    codes_existed = []
    users = Users.query.all()
    for user in users:
        codes_existed.append(user.personal_room_code)

    while True:
        new_code = ""
        for _ in range(20):
            new_code += random.choice(ascii_uppercase)
        
        if new_code not in codes_existed:
            return new_code
        
def getIdFromList(array):
    list_of_id = []
    for i in array:
        if i == "" or i == " ":
            continue

        id = i[: i.index('-')]

        list_of_id.append(id)

    return list_of_id

def findCodeToJoin(friendId, array):
    for i in array:
        if i == "" or i == " ":
            continue

        friendid = i[: i.index('-')]

        if friendid == str(friendId):
            code_to_join = i[i.index('-')+1: ]
            code_to_join = code_to_join.strip()

            return code_to_join

@app.route("/")
def home():
    return redirect(url_for('Login'))

@app.route("/login", methods=["GET", "POST"])
def Login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if username == "" or password == "":
            flash("Please do not leave any field blank!", "danger")
            return redirect(url_for('Login'))
        
        found_user = Users.query.filter_by(username=username).first()

        if found_user != None:
            actual_password = found_user.password

            if password != actual_password:
                flash("That password does not match with the username!", "danger")
                return redirect(url_for('Login'))
            else:
                #if the username exist in the database and the password matches, then log them in
                session['username'] = username
                session['temp_roomcode'] = found_user.personal_room_code
                session['login'] = True
                session['chatter'] = ""
                #let them join their own room
                
                flash("successfully logged in", "success")
                return redirect(url_for("User"))
        else:
            flash('That username does not exist!', 'danger')
            return redirect(url_for('Login'))
    else:
        session['login'] = False
        return render_template("login.html", login=False)

@app.route("/create", methods=["GET", "POST"])
def Create():
    if request.method == "POST":
        new_username = request.form['new_username']
        new_password = request.form['new_password']
        con_password = request.form['con_password']

        if new_username == "" or new_password == "" or con_password == "":      #ensures that no fields in create is left blank
            flash("Please do not leave any field blank!", "danger")
            return redirect(url_for("Create"))
        elif " " in new_username:
            flash("No spaces are allowed in a username!", "danger")
            return redirect(url_for("Create"))
        

        found_user = Users.query.filter_by(username=new_username).first()

        if found_user:
            flash("Username has been taken, please choose another", "danger")
            return redirect(url_for('Create'))
        elif new_password != con_password:
            flash("Password and Confirmation Password do not match, Please try again", "danger")
            return redirect(url_for('Create'))
        else:
            new_code = generateRandomCode()
            new_user = Users(username=new_username, password=new_password, personal_room_code=new_code, friends_list="", friend_requests="")

            db.session.add(new_user)
            db.session.commit()         #new user created
                                        #now go back to login page
            flash("Account successfully created", "success")
            return redirect(url_for('Login'))
        

    return render_template("createAcc.html", login=False)

@app.route("/user", methods = ["GET", "POST"])
def User():
    if session['login'] == False:
        flash("Please Log in to access this page", "warning")
        return redirect(url_for('Login'))
    
    session['partyleader'] = None
    session['partymember'] = None
 
    session['currentlobby'] = None
    return render_template("user.html", login=True, username=session.get('username'))


@app.route("/friends", methods=["GET", "POST"])
def Friends():
    user = Users.query.filter_by(username=session.get('username')).first()

    #grab all of the username from the list_of_friend_requests
    list_of_friend_requests = user.friend_requests
    list_of_ids = list_of_friend_requests.split(" ")

    list_of_user_requested = []

    for i in list_of_ids:
        if i == "" or i == " ":
            continue

        friend = Users.query.filter_by(id=i).first()
        list_of_user_requested.append(friend.username)

    #now grab all of the name of the friends in friends list
    list_of_friends_id = user.friends_list
    list_of_ids = list_of_friends_id.split(" ")

    list_of_friends_name = []

    for i in list_of_ids:
        if i == "" or i == " ":
            continue

        friendname = i[:i.index('-')]
        friend = Users.query.filter_by(id=friendname).first()
        list_of_friends_name.append(friend.username)


    return render_template('friends.html', login=True, personal_room_code = user.personal_room_code, username=session.get('username'), friends=list_of_friends_name, friend_requests=list_of_user_requested)

@app.route("/logout", methods=["POST", "GET"])
def Logout():
    session.clear()
    flash("Successfully Logged out!", "success")
    return redirect(url_for('Login'))

@app.route("/add-friend", methods =["GET", "POST"])
def AddFriend():
    if request.method == "POST":
        self_username = session.get('username')
        friend_username = request.form['friend-name']

        self_obj = Users.query.filter_by(username=self_username).first()
        friend_string = self_obj.friends_list

        friends_list = friend_string.split(" ")
        
        friends_id = []

        for i in friends_list:
            if i == "" or i == " ":
                continue

            friends_id.append(i[:i.index('-')])

        if friend_username == "":
            flash("Please don't leave the input blank", "danger")
            return redirect(url_for('AddFriend'))
        
        found_user = Users.query.filter_by(username=friend_username).first()    #this is the friend

        if not found_user:
            flash("Username does not exist!", "danger")
            return redirect(url_for('AddFriend'))
        elif found_user.username == self_username:
            flash("Can't send friend request to yourself!", "danger")
            return redirect(url_for('AddFriend'))
        elif str(found_user.id) in friends_id:
            flash("User is already friend with you!", "danger")
            return redirect(url_for('AddFriend'))
        else:
            #here send the friend request to the 'friend'
            me = Users.query.filter_by(username=self_username).first()
            found_user.friend_requests += f"{me.id} "
            db.session.commit()

            flash(f"Friend request successfully sent to {friend_username}!", "success")
            return redirect(url_for('Friends'))

    else:
        return render_template("addFriend.html", username=session.get('username'))
    

@app.route("/setup", methods = ["GET", "POST"])
def SetUp():
    data = request.get_json()

    me_obj = Users.query.filter_by(username= session.get('username')).first()
    friend_name = data['friend']

    friend_obj = Users.query.filter_by(username=friend_name).first()
    
    my_friend = me_obj.friends_list
    my_friend_list = my_friend.split(" ")

    code_to_join = None

    for i in my_friend_list:
        if i == "" or i == " ":
            continue

        friendid = i[: i.index('-')]

        if friendid == str(friend_obj.id):
            code_to_join = i[i.index('-')+1: ]
            code_to_join = code_to_join.strip()
            break
            
    session['chatter'] = friend_name

    return {"roomcode": code_to_join}


@app.route("/chat", methods = ["POST", "GET"])
def Chat():
    friend_name = session.get('chatter')
    friend_obj = Users.query.filter_by(username=friend_name).first()

    me_obj = Users.query.filter_by(username=session.get('username')).first()

    #now loop through my friends list to find the ROOM ID to reach friend_obj at

    friend_string = me_obj.friends_list

    friend_list = friend_string.split(" ")

    code = findCodeToJoin(friend_obj.id, friend_list)
    chat = ChatsSaved.query.filter_by(chatroomID=code).first()

    message_holder = chat.chatroomText

    return render_template('chat.html', messages=message_holder, roomcode=code, chattername=session.get('chatter'), username=session.get('username'))


@app.route("/removefriend", methods=["GET", "POST"])
def RemoveFriend():
    #grab the session user and the friend to be removed
    data = request.get_json()

    friend_name = data['friend']
    my_name = session.get('username')

    friend_obj = Users.query.filter_by(username=friend_name).first()
    me_obj = Users.query.filter_by(username = my_name).first()


    #first remove the friend from the session user friend's list
    #then update the table

    friend_string = me_obj.friends_list
    friend_list = friend_string.split(" ")

    code = None       #use this code to remove the chats saved in ChatsSaved

    friend_to_be_removed = None

    for i in friend_list:
        if i == "" or i == " ":
            continue
        print(i)
        id = i[: i.index('-')]  #string id

        if id == str(friend_obj.id):
            #if found then remove i fromm the list
            friend_to_be_removed = i
            break

    if friend_to_be_removed:
        friend_list.remove(friend_to_be_removed)

    space = " "

    new_friend_string = space.join(friend_list).strip()     #remove any uneccasry spaces

    me_obj.friends_list = new_friend_string
    db.session.commit()

    #then remove the session user from the friend's friend_list
    #then update the table

    friend_string = friend_obj.friends_list
    friend_list = friend_string.split(" ")

    friend_to_be_removed = None

    for i in friend_list:
        if i == "" or i == " ":
            continue

        id = i[: i.index('-')]  #string id

        if id == str(me_obj.id):
            #if found then remove i fromm the list
            friend_to_be_removed = i
            code = i[i.index('-')+1:]
            break

    if friend_to_be_removed:
        friend_list.remove(friend_to_be_removed)

    space = " "

    new_friend_string = space.join(friend_list).strip()     #remove any uneccasry spaces

    friend_obj.friends_list = new_friend_string
    db.session.commit()

    #then remove the chats saved of yall's two chat log
    #update the ChatsSaved table
    print(code)
    chatssaved = ChatsSaved.query.filter_by(chatroomID=code).first()

    print(chatssaved)
    db.session.delete(chatssaved)
    db.session.commit()

    return {}      #return to the friends page once everything is updated


@app.route("/createlobby", methods = ["GET", "POST"])
def CreateLobby():
    if request.method == "POST":
        user = Users.query.filter_by(username=session.get('username')).first()

        session['partyleader'] = True
        session['partymember'] = False

        session['currentlobby'] = user.personal_room_code

        #also create a new active lobby object and add it to the database

        new_active_lobby = ActiveLobby(room_code=session.get('currentlobby'), id_of_members="")
        db.session.add(new_active_lobby)
        db.session.commit()

        print("lobby created")
        return redirect(url_for('Lobby'))
        #ONLY delete it when the party leader leaves
    else:
        session['partyleader'] = None
        session['partymember'] = None
 
        session['currentlobby'] = None
        return render_template("createLobby.html", login=True, username=session.get('username'))


@app.route("/joinlobby", methods =["POST", "GET"])
def JoinLobby():
    if request.method == "POST":
        #join the user inputted lobby code
        #but first check if its valid or empty
        userInputCode = request.form['user_input_lobby_code']

        if userInputCode == "" or userInputCode == " ":
            flash("Please do not leave the field blank!", "danger")
            return redirect(url_for('JoinLobby'))
        
        lobby_found = ActiveLobby.query.filter_by(room_code=userInputCode).first()

        if lobby_found == None:
            flash("Not a valid room code!", "danger")
            return redirect(url_for('JoinLobby'))
        else:
            #a valid room is found, so join it
            session['partyleader'] = False
            session['partymember'] = True
 
            session['currentlobby'] = lobby_found.room_code

            return redirect(url_for('Lobby'))

    else:
        session['partyleader'] = None
        session['partymember'] = None
 
        session['currentlobby'] = None
        return render_template("joinLobby.html", login=True, username=session.get('username'))


@app.route("/lobby", methods = ["GET", "POST"])
def Lobby():
    if session.get('currentlobby') == None:
        flash('Please Create A Party or Join One Before Accessing This Page!', "danger")
        return redirect(url_for('User'))

    user = Users.query.filter_by(username=session.get('username')).first()
    return render_template("lobby.html", userid=user.id, username=session.get('username'), lobbycode = session.get('currentlobby'), partyleader = session.get('partyleader'), partymember = session.get('partymember'))



@app.route("/topics", methods=["GET", "POST"])
def Topics():
    user = Users.query.filter_by(username=session.get('username')).first()
    return render_template('topics.html', userid=user.id, username=session.get('username'), lobbycode = session.get('currentlobby'), partyleader = session.get('partyleader'), partymember = session.get('partymember'))


#========================= SOCKETS ==============================================#

@socketio.on("loggedin")  #MIGHT LEAD TO PROBLEMS
def loggedin(obj):
    user = Users.query.filter_by(username=session.get('username')).first()
    room_code = user.personal_room_code
    print(room_code)
    join_room(room_code)
    
    print(f"{user.username} has joined room {room_code}")

@socketio.on("accept")
def message(obj):
    me = session.get('username') #current user username
    friend = obj['friend']      #friend sending the friend request
    code_for_both = generateRandomCode()

    me_obj = Users.query.filter_by(username=me).first()
    friend_obj = Users.query.filter_by(username=friend).first()

    #if accepted, remove the friend request from my own friend request list (NOT THE FRIEND SINCE NO ONE SEND IT TO THEM)
    str_of_friend_request = me_obj.friend_requests

    list_of_id_of_request = list(str_of_friend_request.split(" "))

    list_of_id_of_request.remove(str(friend_obj.id))

    space = " "
    new_list_of_id_of_request = space.join(list_of_id_of_request)

    me_obj.friend_requests = new_list_of_id_of_request
    db.session.commit()

    #now add the friend my list of friends and myself to their list of friends
    me_obj.friends_list += f"{friend_obj.id}-{code_for_both} "
    db.session.commit()

    friend_obj.friends_list += f"{me_obj.id}-{code_for_both} "
    db.session.commit()

    #now create a new chat saved object to store the chats between the two

    newChat = ChatsSaved(chatroomID=code_for_both, chatroomTexts="")

    db.session.add(newChat)
    db.session.commit()

    socketio.emit(f"requests{me_obj.personal_room_code}", {"friend" : f"{friend}", "message" : "Friend Request Accepted", "category" : "success"})

@socketio.on("decline")
def message(obj):
    me = session.get('username') #current user username
    friend = obj['friend']

    me_obj = Users.query.filter_by(username=me).first()
    friend_obj = Users.query.filter_by(username=friend).first()

    #if declined, remove the friend request from my own friend request list
    list_of_friend_request = me_obj.friend_requests

    list_of_id_of_request = list(list_of_friend_request.split(" "))

    list_of_id_of_request.remove(str(friend_obj.id))

    space = " "
    new_list_of_id_of_request = space.join(list_of_id_of_request)

    me_obj.friend_requests = new_list_of_id_of_request
    db.session.commit()

    socketio.emit(f"requests{me_obj.personal_room_code}", {"friend" : f"{friend}", "message" : "Friend Request Declined", "category" : "success"})


@socketio.on("joinroom")
def join(obj):
    join_room(obj['roomcode'])

    me = session.get('username') #current user username
    me_obj = Users.query.filter_by(username=me).first()

    print(f"{me} joined room {obj['roomcode']}")
    socketio.emit(f"joined{me_obj.personal_room_code}", { "roomcode": obj['roomcode']})

@socketio.on("message")
def message(obj):
    friend_name = obj['friend']
    friend_obj = Users.query.filter_by(username=friend_name).first()

    me_obj = Users.query.filter_by(username=session.get('username')).first()

    #now loop through my friends list to find the ROOM ID to reach friend_obj at

    friend_string = me_obj.friends_list

    friend_list = friend_string.split(" ")

    code = findCodeToJoin(friend_obj.id, friend_list)

    #now save their chat to the ChatsSaved table
    chatsaved = ChatsSaved.query.filter_by(chatroomID=code).first()
    chatsaved.chatroomText += f"{obj['name']}~&{obj['message']}&`"   #COMEBACK TO IN A FEW MIN
    # messages are split by '&`' so split them using '&`'
    # separated by ~&
    db.session.commit()

    socketio.emit(f"{code}", {"username" : obj['name'], "message": obj['message']})


@socketio.on("join-lobby")
def JoinLobby(obj):
    member = Users.query.filter_by(username=obj['username']).first()
    
    lobby_code = obj['lobbycode']
    active_lobby_found = ActiveLobby.query.filter_by(room_code=lobby_code).first()

    if obj['username'] != 'None':

        #let 'member' join the lobby room
        join_room(lobby_code)
        print(f"{obj['username']} joined lobby {obj['lobbycode']}")
        #CHECK IF THEYRE ALREADY IN THE LOBBY, IF SO DONT ADD THEM AGAIN

        #here, add their id to the active lobby of 'lobby_code

        string_of_members = active_lobby_found.id_of_members
        list_of_members = string_of_members.split("-")

        if str(member.id) not in list_of_members:
            active_lobby_found.id_of_members += f"{member.id}-"
            db.session.commit()

    
    string_of_members = active_lobby_found.id_of_members
    list_of_members = string_of_members.split("-")

    list_of_members_name = []

    for member in list_of_members:
        if member == "" or member == " ":
            continue

        user = Users.query.filter_by(id=member).first()
        list_of_members_name.append(user.username)

    #now send the list of usernames back to the frontend
    #then emit back to "joined{{lobbycode}}" that "user" joined the lobby

    socketio.emit(f"joined{lobby_code}", {"usernames" : list_of_members_name})


@socketio.on("leave-lobby")
def LeaveLobby(obj):
    
    username = obj['user']
    lobby_code = obj['code']

    user_obj = Users.query.filter_by(username=username).first()
    lobby_found = ActiveLobby.query.filter_by(room_code=lobby_code).first()

    #if user_obj personal room code is equal to lobby found, then that is the party leader
    #if so, first grab the list of all username from the list of id and pass it back to the frontend
    #then delete the lobby found, while the frontend sends everyone in the lobby back to the home page
    #emit back an event of 'x-{{lobbycode}}'
    if str(user_obj.personal_room_code) == lobby_code:
        string_of_members = lobby_found.id_of_members

        list_of_members = string_of_members.split("-")

        list_of_members_name = []

        for i in list_of_members: #this is list of ids
            if i == "" or i == " ":
                continue

            user = Users.query.filter_by(id = int(i)).first()
            list_of_members_name.append(user.username)

        
        db.session.delete(lobby_found)
        db.session.commit()

        socketio.emit(f"delete-lobby{lobby_code}", {'remaining_members' : list_of_members_name})


    #else, this is a member leaving, and it will get a special emit of 'x-{{lobbycode}}-{{username}}'
    #first grab the id of the user and remove it from the list of ids of members of the active lobby
    #save those changes
    #then emit back a new list of members to be displayed along with 'x-{{lobbycode}}-{{username}}'
    else:
        id_of_user = str(user_obj.id)

        string_of_id_of_members = lobby_found.id_of_members
        list_of_id_of_members = string_of_id_of_members.split('-')

        id_to_be_removed = ""

        for i in list_of_id_of_members:
            if str(i) == "" or str(i) == " ":
                continue

            if str(i) == id_of_user:
                id_to_be_removed = str(i)
                break

        list_of_id_of_members.remove(str(id_to_be_removed))

        dash = '-'
        new_string = dash.join(list_of_id_of_members)

        lobby_found.id_of_members = new_string.strip()
        db.session.commit()

        new_string_of_members = lobby_found.id_of_members
        new_list_of_members = new_string_of_members.split('-')

        list_of_remaining_members = []

        for i in new_list_of_members:
            if i == "" or i == " ":
                continue

            user = Users.query.filter_by(id=int(i)).first()

            list_of_remaining_members.append(str(user.username))

        #now emit back a special event along with the list
        socketio.emit(f"leave-lobby{lobby_code}{username}", {'remaining_members' : list_of_id_of_members})


@socketio.on("message-lobby")
def MessageLobby(obj):
    lobbycode = obj['lobby_code']
    socketio.emit(f"lobby{lobbycode}", {"username" : obj['name'], "message": obj['message']})

@socketio.on("select-topics")
def SelectTopic(obj):
    print(f"{obj['lobbycode']} wants to go to select topics")    



