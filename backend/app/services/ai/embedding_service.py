"""Embedding 服务。

基于 sentence-transformers 的文本向量化，使用 bge-small-zh-v1.5 模型。
懒加载模型，首次调用时才初始化。
"""

import logging
from typing import TYPE_CHECKING

import numpy as np

from app.core.config import settings

if TYPE_CHECKING:
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)

_model = None
_model_loaded = False


def _get_model():
    """懒加载 embedding 模型。"""
    global _model, _model_loaded
    if _model_loaded:
        return _model

    _model_loaded = True
    try:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", settings.embedding_model)
        _model = SentenceTransformer(
            settings.embedding_model,
            device=settings.embedding_device,
            cache_folder=settings.embedding_cache_dir,
        )
        logger.info("Embedding model loaded successfully (dim=%d)", settings.embedding_dimension)
    except ImportError:
        logger.warning("sentence-transformers not installed; embedding service disabled")
        _model = None
    except Exception:
        logger.exception("Failed to load embedding model")
        _model = None

    return _model


def is_available() -> bool:
    """检查 embedding 服务是否可用。"""
    return _get_model() is not None


def encode_texts(texts: list[str], normalize: bool = True) -> list[list[float]]:
    """批量编码文本为向量。

    Args:
        texts: 文本列表
        normalize: 是否 L2 归一化（推荐，用于余弦相似度）

    Returns:
        向量列表，每个向量长度为 embedding_dimension
    """
    model = _get_model()
    if model is None:
        return [[] for _ in texts]

    embeddings = model.encode(texts, normalize_embeddings=normalize, show_progress_bar=False)
    return [emb.tolist() for emb in embeddings]


def encode_single(text: str, normalize: bool = True) -> list[float]:
    """编码单条文本为向量。"""
    results = encode_texts([text], normalize=normalize)
    return results[0] if results else []
