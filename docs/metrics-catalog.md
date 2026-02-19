# LLM 推理服务监控指标目录

## 第一层：GPU 硬件层（DCGM Exporter 采集）

| 指标名 | 含义 | 单位 | 告警阈值建议 |
|--------|------|------|-------------|
| DCGM_FI_DEV_GPU_UTIL | GPU 计算核心利用率 | % | >95% 持续5分钟 |
| DCGM_FI_DEV_FB_USED | 已使用显存 | MiB | >90% 总显存 |
| DCGM_FI_DEV_FB_FREE | 可用显存 | MiB | <2048MiB |
| DCGM_FI_DEV_GPU_TEMP | GPU 温度 | ℃ | >80℃ |
| DCGM_FI_DEV_POWER_USAGE | GPU 功耗 | W | >140W (A10) |
| DCGM_FI_DEV_SM_CLOCK | SM 时钟频率 | MHz | 降频告警 |
| DCGM_FI_DEV_MEM_CLOCK | 显存时钟频率 | MHz | 降频告警 |
| DCGM_FI_DEV_PCIE_TX_THROUGHPUT | PCIe 发送带宽 | bytes/s | 信息采集 |
| DCGM_FI_DEV_PCIE_RX_THROUGHPUT | PCIe 接收带宽 | bytes/s | 信息采集 |
| DCGM_FI_DEV_ECC_SBE_VOL_TOTAL | ECC 单比特错误 | count | >0 |
| DCGM_FI_DEV_ECC_DBE_VOL_TOTAL | ECC 双比特错误 | count | >0（严重） |

## 第二层：推理服务层（vLLM 原生 + 自定义 Exporter 采集）

### vLLM 原生暴露的指标

| 指标名 | 含义 | 类型 |
|--------|------|------|
| vllm:e2e_request_latency_seconds | 端到端请求延迟 | Histogram |
| vllm:num_requests_running | 正在处理的请求数 | Gauge |
| vllm:num_requests_waiting | 等待中的请求数 | Gauge |
| vllm:num_preemptions_total | 抢占次数 | Counter |
| vllm:gpu_cache_usage_perc | GPU KV Cache 使用率 | Gauge |
| vllm:cpu_cache_usage_perc | CPU KV Cache 使用率 | Gauge |
| vllm:prompt_tokens_total | 输入 Token 总数 | Counter |
| vllm:generation_tokens_total | 生成 Token 总数 | Counter |
| vllm:time_to_first_token_seconds | 首 Token 延迟（TTFT） | Histogram |
| vllm:time_per_output_token_seconds | 每个输出 Token 耗时 | Histogram |

### 自定义 Exporter 补充采集的指标

| 指标名 | 含义 | 来源 |
|--------|------|------|
| vllm_model_loaded | 模型是否加载完成 | /health 端点 |
| vllm_available_models | 可用模型数量 | /v1/models 端点 |
| vllm_request_success_total | 成功请求计数 | /v1/chat/completions |
| vllm_request_error_total | 失败请求计数（按错误类型） | /v1/chat/completions |
| vllm_input_tokens_per_request | 每请求输入 Token 数分布 | /v1/chat/completions |
| vllm_output_tokens_per_request | 每请求输出 Token 数分布 | /v1/chat/completions |

## 第三层：业务层（自定义 Exporter + Prometheus 规则计算）

| 指标/规则 | 含义 | 计算方式 |
|-----------|------|---------|
| QPS | 每秒请求数 | rate(vllm:e2e_request_latency_seconds_count[1m]) |
| 请求成功率 | 成功/总数 | 1 - (error_total / total_requests) |
| P50/P95/P99 延迟 | 延迟分位数 | histogram_quantile(0.99, ...) |
| Token 吞吐量 | 每秒生成 Token 数 | rate(vllm:generation_tokens_total[1m]) |
| KV Cache 耗尽风险 | Cache 使用率趋势 | predict_linear(gpu_cache_usage[10m], 300) |
