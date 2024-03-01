from theboys import db

class Users(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    username = db.Column("username", db.String(50), unique=True, nullable=False)
    password = db.Column("password", db.String(50), nullable=False)
    personal_room_code = db.Column("personal_room_code", db.String(30))
    friends_list = db.Column("friends_list", db.String(200))
    friend_requests = db.Column("friend_requests", db.String(200))

    def __init__(self, username, password, personal_room_code, friends_list, friend_requests):
        self.username = username
        self.password = password
        self.personal_room_code = personal_room_code
        self.friends_list = friends_list                #default will be an empty string => ""
        self.friend_requests = friend_requests          #default will be an empty string => ""


class ChatsSaved(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    chatroomID = db.Column("chatroomID", db.String(30), nullable=False)
    chatroomText = db.Column("chatroomTexts", db.Text(), nullable=False)

    def __init__(self, chatroomID, chatroomTexts):
        self.chatroomID = chatroomID
        self.chatroomText = chatroomTexts               #default will be an empty text => ""
                                                        #this will be used when new friendship established 
                                                        #AND new groupchat created

class ActiveLobby(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    room_code = db.Column("room_code", db.String(30), nullable=False)
    id_of_members = db.Column("id_of_members", db.Text(), nullable=False)

    def __init__(self, room_code, id_of_members):
        self.room_code = room_code
        self.id_of_members = id_of_members


