from services.sign_language_model import predict_sign
from services.emotion_detector import predict_emotion

def predict_all(frame):
    sign = predict_sign(frame)
    emotion = predict_emotion(frame)

    return {
        "sign": sign,
        "emotion": emotion
    }