from theboys import socketio, app, db
from theboys.models import Users, ChatsSaved, ActiveLobby

if __name__ == "__main__":
    socketio.run(app, debug=True)


