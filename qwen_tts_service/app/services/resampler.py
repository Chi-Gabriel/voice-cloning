import os
import logging
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Tuple
import soundfile as sf
import numpy as np
from math import gcd
from app.core.config import settings

logger = logging.getLogger(__name__)

class ResamplerService:
    def __init__(self, target_sr: int = None, max_workers: int = None):
        self.target_sr = target_sr or settings.RESAMPLE_TARGET_SR
        self.max_workers = max_workers or settings.RESAMPLE_MAX_WORKERS
        self.storage_dir = Path("/tmp/tts_files")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def resample_files(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Resample a list of files in parallel. 
        Returns a map of {old_path: new_path}.
        Old files are deleted.
        """
        results = {}
        if not file_paths:
            return results

        logger.info(f"Resampling {len(file_paths)} files to {self.target_sr}Hz with {self.max_workers} workers")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {executor.submit(self._resample_single, path): path for path in file_paths}
            for future in concurrent.futures.as_completed(future_to_path):
                old_path = future_to_path[future]
                try:
                    new_path = future.result()
                    results[old_path] = new_path
                    # Delete original if it's different from the new one
                    if old_path != new_path and os.path.exists(old_path):
                        os.remove(old_path)
                except Exception as e:
                    logger.error(f"Failed to resample {old_path}: {e}")
                    # In case of failure, we might want to keep the old path in the map?
                    # But the requirement says "returns a map of old files to new counterparts"
                    # If it failed, we keep the original as the "new" one to avoid breaking the pipeline.
                    results[old_path] = old_path

        return results

    def _resample_single(self, path: str) -> str:
        """Worker function for resampling a single file."""
        try:
            data, sr = sf.read(path)
            if sr == self.target_sr:
                return path

            # Convert to float32 [C, S] for processing
            if data.ndim == 1:
                x_cs = data[None, :]
            else:
                x_cs = data.T # [S, C] -> [C, S]

            # HQ Resample
            out_cs = self._resample_hq(x_cs, sr, self.target_sr)

            # Convert back to [S, C] for soundfile
            out_sc = out_cs.T

            # Save new file
            p = Path(path)
            new_path = str(p.parent / f"{p.stem}_{self.target_sr}hz{p.suffix}")
            sf.write(new_path, out_sc, self.target_sr)
            
            return new_path
        except Exception as e:
            logger.error(f"Error in _resample_single for {path}: {e}")
            raise e

    def _resample_hq(self, x_cs: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
        """
        HQ resampling cascade: soxr -> scipy.signal.resample_poly -> torchaudio -> linear.
        Adapted from Egregora audio node.
        """
        if src_sr == dst_sr:
            return x_cs.astype(np.float32)

        # soxr
        try:
            import soxr
            out = [soxr.resample(x_cs[c], src_sr, dst_sr) for c in range(x_cs.shape[0])]
            L = min(map(len, out))
            out = np.stack([ch[:L] for ch in out], axis=0)
            return out.astype(np.float32)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"soxr resampling failed: {e}")

        # SciPy polyphase
        try:
            from scipy.signal import resample_poly
            g = gcd(src_sr, dst_sr)
            up, down = dst_sr // g, src_sr // g
            out = [resample_poly(x_cs[c], up=up, down=down).astype(np.float32) for c in range(x_cs.shape[0])]
            L = min(map(len, out))
            out = np.stack([ch[:L] for ch in out], axis=0)
            return out
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"scipy resampling failed: {e}")

        # torchaudio windowed-sinc
        try:
            import torch
            import torchaudio
            t = torch.from_numpy(x_cs).float()
            rs = torchaudio.transforms.Resample(orig_freq=src_sr, new_freq=dst_sr)
            y = rs(t)
            return y.numpy().astype(np.float32)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"torchaudio resampling failed: {e}")

        # linear interp fallback
        ratio = dst_sr / float(src_sr)
        n_out = int(round(x_cs.shape[1] * ratio))
        t_in = np.linspace(0.0, 1.0, x_cs.shape[1], endpoint=False, dtype=np.float64)
        t_out = np.linspace(0.0, 1.0, n_out, endpoint=False, dtype=np.float64)
        out = np.stack([np.interp(t_out, t_in, ch) for ch in x_cs], axis=0).astype(np.float32)
        return out

resampler = ResamplerService()
