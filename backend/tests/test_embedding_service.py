"""Embedding 服务单元测试。"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.ai.embedding_service import is_available, encode_texts, encode_single

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class TestEmbeddingService:
    """embedding_service 测试。"""

    def test_is_available_when_not_installed(self):
        """sentence-transformers 未安装时返回 False。"""
        result = is_available()
        assert result is False

    def test_encode_texts_returns_empty_when_unavailable(self):
        """服务不可用时返回空向量列表。"""
        with patch("app.services.ai.embedding_service._get_model", return_value=None):
            result = encode_texts(["hello", "world"])
            assert result == [[], []]

    def test_encode_single_returns_empty_when_unavailable(self):
        """服务不可用时返回空向量。"""
        with patch("app.services.ai.embedding_service._get_model", return_value=None):
            result = encode_single("hello")
            assert result == []

    @pytest.mark.skipif(not HAS_NUMPY, reason="numpy not installed")
    def test_encode_texts_with_mock_model(self):
        """使用 mock 模型测试批量编码。"""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])

        with patch("app.services.ai.embedding_service._get_model", return_value=mock_model):
            result = encode_texts(["hello", "world"])
            assert len(result) == 2
            assert len(result[0]) == 3
            mock_model.encode.assert_called_once()

    @pytest.mark.skipif(not HAS_NUMPY, reason="numpy not installed")
    def test_encode_single_with_mock_model(self):
        """使用 mock 模型测试单条编码。"""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])

        with patch("app.services.ai.embedding_service._get_model", return_value=mock_model):
            result = encode_single("hello")
            assert len(result) == 3
            assert abs(result[0] - 0.1) < 1e-6
