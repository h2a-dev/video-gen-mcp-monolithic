"""Simple file upload caching service to avoid duplicate uploads."""

import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import aiofiles
from datetime import datetime, timedelta

class FileUploadCache:
    """
    Simple LRU cache for file uploads to avoid re-uploading the same files.
    Caches file hash -> URL mappings.
    """
    
    def __init__(self, max_size: int = 100, ttl_hours: int = 24):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of cached entries
            ttl_hours: Time-to-live for cache entries in hours
        """
        self._cache: Dict[str, Dict[str, Any]] = {}  # hash -> {url, timestamp}
        self._max_size = max_size
        self._ttl = timedelta(hours=ttl_hours)
        self._lock = asyncio.Lock()
    
    async def get_or_upload(self, file_path: str, upload_func) -> Dict[str, Any]:
        """
        Get cached URL or upload file and cache the result.
        
        Args:
            file_path: Path to the file
            upload_func: Async function to upload the file
            
        Returns:
            Dict with success status, URL, and cache hit info
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            if not path.is_file():
                return {
                    "success": False,
                    "error": f"Path is not a file: {file_path}"
                }
            
            # Calculate file hash
            file_hash = await self._calculate_file_hash(path)
            
            # Check cache
            async with self._lock:
                cached = self._get_cached_url(file_hash)
                if cached:
                    return {
                        "success": True,
                        "url": cached,
                        "cached": True,
                        "original_path": file_path,
                        "file_hash": file_hash
                    }
            
            # Upload file
            upload_result = await upload_func(file_path)
            
            if not upload_result.get("success", False):
                return upload_result
            
            # Cache the result
            url = upload_result.get("url")
            if url:
                async with self._lock:
                    await self._add_to_cache(file_hash, url)
            
            return {
                "success": True,
                "url": url,
                "cached": False,
                "original_path": file_path,
                "file_hash": file_hash
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Cache operation failed: {str(e)}"
            }
    
    async def _calculate_file_hash(self, path: Path) -> str:
        """Calculate SHA256 hash of file content asynchronously."""
        sha256_hash = hashlib.sha256()
        
        async with aiofiles.open(path, 'rb') as f:
            # Read in chunks to handle large files
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _get_cached_url(self, file_hash: str) -> Optional[str]:
        """Get URL from cache if it exists and is not expired."""
        if file_hash not in self._cache:
            return None
        
        entry = self._cache[file_hash]
        timestamp = entry["timestamp"]
        
        # Check if expired
        if datetime.now() - timestamp > self._ttl:
            del self._cache[file_hash]
            return None
        
        # Move to end (LRU behavior)
        del self._cache[file_hash]
        self._cache[file_hash] = entry
        
        return entry["url"]
    
    async def _add_to_cache(self, file_hash: str, url: str):
        """Add URL to cache, enforcing size limit."""
        # Remove oldest entries if at capacity
        if len(self._cache) >= self._max_size:
            # Remove the first (oldest) entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        # Add new entry
        self._cache[file_hash] = {
            "url": url,
            "timestamp": datetime.now()
        }
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_hours": self._ttl.total_seconds() / 3600,
            "oldest_entry": min(
                (entry["timestamp"] for entry in self._cache.values()),
                default=None
            )
        }