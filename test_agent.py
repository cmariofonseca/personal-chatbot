from app.core.agent import Me

def test_chat():
    me = Me()
    response = me.chat("Hola, cuéntame sobre tu experiencia")
    print("Respuesta del chatbot:", response)

if __name__ == "__main__":
    test_chat()