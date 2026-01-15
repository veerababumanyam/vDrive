"""Kafka consumers for processing service."""

from .base_consumer import BaseConsumer
from .asset_processor import AssetProcessor

__all__ = ["BaseConsumer", "AssetProcessor"]
