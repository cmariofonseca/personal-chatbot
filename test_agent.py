from app.core.agent import Me

def test_chat():
    me = Me()
    response = me.chat("cuanto tiempo de experiencia tienes con Angular")
    print("Respuesta del chatbot:", response)

if __name__ == "__main__":
    test_chat()