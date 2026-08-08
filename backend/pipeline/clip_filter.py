import torch
import open_clip
from PIL import Image

HIGH_SIGNAL = [
    "an aerial drone shot looking down at landscape from above",
    "a panoramic landscape with mountains, hills, or valleys",
    "a road, highway, or path with visible markings or signs",
    "a building, temple, church, mosque, or distinctive architecture",
    "text, signage, or writing visible in the scene",
    "a coastline, beach, river, lake, or waterfall",
    "a village, town, or city street view",
    "a railway, bridge, or infrastructure",
]

LOW_SIGNAL = [
    "a close-up of food, fruits, or a meal on a plate",
    "hands cooking, cutting, or preparing food",
    "a person talking to camera, a face portrait",
    "an indoor kitchen scene with pots and utensils",
    "a dark or blurry frame with no clear content",
    "a close-up of a single plant, flower, or fruit on a tree",
]

ALL_CATEGORIES = HIGH_SIGNAL + LOW_SIGNAL


def load_clip():
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model.eval()

    tokens = tokenizer(ALL_CATEGORIES)
    with torch.no_grad():
        text_features = model.encode_text(tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)

    return model, preprocess, text_features


def classify_frame(image: Image.Image, model, preprocess, text_features) -> dict:
    img_tensor = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        img_features = model.encode_image(img_tensor)
        img_features /= img_features.norm(dim=-1, keepdim=True)
        similarities = (img_features @ text_features.T).squeeze(0).numpy()

    scores = {cat: float(sim) for cat, sim in zip(ALL_CATEGORIES, similarities)}

    best_high = max(HIGH_SIGNAL, key=lambda c: scores[c])
    best_low = max(LOW_SIGNAL, key=lambda c: scores[c])
    geo_score = scores[best_high] - scores[best_low]
    is_high_signal = scores[best_high] > scores[best_low]

    return {
        "is_high_signal": is_high_signal,
        "geo_score": round(geo_score, 4),
        "best_category": best_high.split(",")[0].replace("an ", "").replace("a ", "").strip(),
        "best_high_score": round(scores[best_high], 4),
        "best_low_score": round(scores[best_low], 4),
    }
