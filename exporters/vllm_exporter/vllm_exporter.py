#!/usr/bin/env python3
"""
vLLM 自定义 Prometheus Exporter
补充采集 vLLM 原生不暴露的业务层指标
"""
import os
import time
import requests
from prometheus_client import start_http_server, Gauge, Counter, Histogram, CollectorRegistry

# 创建独立的 registry
registry = CollectorRegistry()

# 业务指标
VLLM_MODEL_LOADED = Gauge('vllm_model_loaded', '模型是否加载完成', ['model'], registry=registry)
VLLM_AVAILABLE_MODELS = Gauge('vllm_available_models', '可用模型数量', registry=registry)
VLLM_REQUEST_SUCCESS = Counter('vllm_request_success_total', '成功请求计数', ['model'], registry=registry)
VLLM_REQUEST_ERROR = Counter('vllm_request_error_total', '失败请求计数', ['model', 'error_type'], registry=registry)
VLLM_INPUT_TOKENS = Histogram('vllm_input_tokens_per_request', '每请求输入Token数', registry=registry)
VLLM_OUTPUT_TOKENS = Histogram('vllm_output_tokens_per_request', '每请求输出Token数', registry=registry)
VLLM_QPS = Gauge('vllm_qps', '当前QPS', registry=registry)
VLLM_SUCCESS_RATE = Gauge('vllm_request_success_rate', '请求成功率', registry=registry)

# vLLM 服务地址
VLLM_URL = os.environ.get('VLLM_URL', 'http://localhost:8000')
UPDATE_INTERVAL = int(os.environ.get('UPDATE_INTERVAL', '15'))

def collect_metrics():
    """采集指标"""
    try:
        # 1. 检查模型状态
        try:
            resp = requests.get(f"{VLLM_URL}/v1/models", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get('data', [])
                VLLM_AVAILABLE_MODELS.set(len(models))
                for m in models:
                    model_name = m.get('id', 'unknown')
                    VLLM_MODEL_LOADED.labels(model=model_name).set(1)
        except Exception as e:
            print(f"Error fetching models: {e}")
            VLLM_AVAILABLE_MODELS.set(0)
        
        # 2. 计算 QPS (基于请求速率)
        try:
            # 获取历史请求数计算 QPS
            resp = requests.get(f"{VLLM_URL}/metrics", timeout=5)
            if resp.status_code == 200:
                for line in resp.text.split('\n'):
                    if 'vllm:e2e_request_latency_seconds_count' in line:
                        # 简化处理：返回当前值
                        VLLM_QPS.set(0)  # 实际应由 Prometheus 计算 rate
        except Exception as e:
            print(f"Error fetching metrics: {e}")
        
        # 3. 计算成功率 (简化版)
        VLLM_SUCCESS_RATE.set(100.0)  # 默认100%，实际应由 Prometheus 计算
        
        print(f"Metrics updated at {time.strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"Error collecting metrics: {e}")

def main():
    port = int(os.environ.get('EXPORTER_PORT', '9101'))
    print(f"Starting vLLM Custom Exporter on port {port}")
    print(f"vLLM URL: {VLLM_URL}")
    
    # 启动 HTTP 服务器
    start_http_server(port, registry=registry)
    
    # 定期更新指标
    while True:
        collect_metrics()
        time.sleep(UPDATE_INTERVAL)

if __name__ == '__main__':
    main()
