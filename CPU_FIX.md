# CPU 환경 호환성 수정

## 문제

CPU 환경에서 실행 시 CUDA 관련 오류 발생:
1. `transformer.py`에서 하드코딩된 `'cuda'` 사용
2. `test.py`에서 `torch.cuda.amp.autocast()` 사용

## 수정 내용

### 1. transformer.py (509번째 줄)
```python
# 수정 전
out_attn = torch.zeros([H, H]).to('cuda')

# 수정 후
out_attn = torch.zeros([H, H], device=x.device, dtype=x.dtype)
```

### 2. test.py (159, 177번째 줄)
```python
# 수정 전
with torch.cuda.amp.autocast(), torch.no_grad():

# 수정 후
with torch.amp.autocast(device_type=device.split(':')[0] if ':' in device else device), torch.no_grad():
```

## 결과

이제 CPU 환경에서도 정상적으로 실행됩니다.


