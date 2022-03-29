from typing import List, Optional, Dict, Tuple, Sequence
import ctypes
import numpy as np
from hidet.ir.layout import DataLayout
from hidet.ir.layout.data_layout import RowMajorLayout, ColumnMajorLayout
from hidet.runtime import Storage
from hidet.utils import prod
from hidet.ffi.cuda_api import CudaAPI


def convert(v):
    if isinstance(v, float):
        return full(shape=[1], fill_value=v, dtype='float32')
    elif isinstance(v, Tensor):
        return v
    else:
        raise NotImplementedError()


class Tensor:
    def __init__(self,
                 shape: Sequence[int],
                 dtype: str,
                 device: str,
                 storage: Storage,
                 layout: DataLayout = None,
                 trace: Optional[Tuple['Operator', int]] = None):
        self.shape = [int(v) for v in shape]
        self.dtype = str(dtype)
        self.device = device
        self.storage = storage
        self.layout = layout if layout else DataLayout.row_major(shape)
        self.trace = trace

    def __add__(self, other):
        from .ops import add
        return add(self, convert(other))

    def __sub__(self, other):
        from .ops import sub
        return sub(self, convert(other))

    def __mul__(self, other):
        from .ops import multiply
        return multiply(self, convert(other))

    def __truediv__(self, other):
        from .ops import divide
        return divide(self, convert(other))

    def __str__(self):
        return "Tensor(shape={}, dtype='{}', device='{}')\n{}".format(
            self.shape, self.dtype, self.device, str(self.cpu().numpy())
        )

    def contiguous(self):
        if isinstance(self.layout, RowMajorLayout):
            return self
        return self.reshape(self.shape)

    def reshape(self, shape):
        from .ops import reshape
        return reshape(self, shape)

    def flatten(self, start_dim=0, end_dim=-1):
        from .ops import flatten
        return flatten(self, start_dim, end_dim)

    def rsqrt(self):
        from .ops import rsqrt
        return rsqrt(self)

    def cpu(self):
        if self.device == 'cpu':
            return self
        else:
            if self.trace is None:
                return Tensor(self.shape, self.dtype, 'cpu', self.storage.cpu(), self.layout)
            else:
                # lazy mode related
                raise NotImplementedError()

    def cuda(self):
        if self.device == 'cuda':
            return self
        else:
            if self.trace is None:
                return Tensor(self.shape, self.dtype, 'cuda', self.storage.cuda(), self.layout)
            else:
                # lazy mode related
                raise NotImplementedError()

    def numpy(self) -> np.ndarray:
        if self.device != 'cpu':
            raise ValueError('Please use .cpu() to move data from {} to cpu first.'.format(self.device))
        # convert if this tensor is not in row major layout
        storage = self.contiguous().storage
        array = storage.as_array(dtype=self.dtype)
        return array.reshape(self.shape)


def dtype_bytes(dtype: str):
    bytes_dict = {
        'float32': 4
    }
    return bytes_dict[dtype]


def empty(shape: Sequence[int], dtype: str = 'float32', device: str = 'cuda', layout: Optional[DataLayout] = None) -> Tensor:
    num_bytes = prod(shape) * dtype_bytes(dtype)
    storage = Storage.new(device, num_bytes)
    return Tensor(shape, dtype, device, storage, layout)


def zeros(shape: Sequence[int], dtype: str = 'float32', device: str = 'cuda', layout: Optional[DataLayout] = None) -> Tensor:
    tensor = empty(shape, dtype, device, layout)
    CudaAPI.memset_async(tensor.storage.addr, tensor.storage.num_bytes, value=0)
    return tensor


def ones(shape: Sequence[int], dtype: str = 'float32', device: str = 'cuda', layout: Optional[DataLayout] = None) -> Tensor:
    return full(shape, 1.0, dtype, device, layout)


def full(shape: Sequence[int], fill_value, dtype: str = 'float32', device: str = 'cuda', layout: Optional[DataLayout] = None) -> Tensor:
    tensor = empty(shape, dtype, device, layout)
    if dtype == 'float32':
        CudaAPI.fill_value(tensor.storage.addr, tensor.storage.num_bytes, value=fill_value)
    else:
        raise NotImplementedError()
    return tensor


def randn(shape: Sequence[int], dtype: str = 'float32', mean: float = 0.0, stddev: float = 1.0, device: str = 'cuda', layout: Optional[DataLayout] = None) -> Tensor:
    tensor = empty(shape, dtype, device, layout)
    if dtype == 'float32':
        CudaAPI.generate_normal(tensor.storage.addr, prod(tensor.shape), mean, stddev)
    else:
        raise NotImplementedError()
    return tensor


def void_pointer_to_uint64(p):
    ret = ctypes.cast(ctypes.addressof(p), ctypes.POINTER(ctypes.c_uint64)).contents
    return ret.value


def from_numpy(array: np.ndarray) -> Tensor:
    if array.dtype == np.float32:
        tensor = empty(shape=array.shape, dtype='float32', device='cpu')
        CudaAPI.memcpy_async(void_pointer_to_uint64(array.ctypes.data_as(ctypes.c_void_p)),
                             tensor.storage.addr,
                             tensor.storage.num_bytes,
                             CudaAPI.HostToHost)
        CudaAPI.device_synchronization()
        return tensor
    else:
        raise NotImplementedError('')
