# 安装依赖
 ```bash
 pip install -r requirements.txt
 ```

# 设置环境变量
```bash
export CHAIN="Polkadot Asset Hub"
export URL="wss://polkadot-asset-hub-rpc.polkadot.io"

export HOST=localhost
export MYSQLUSER="root"
export PASSWORD="password"
export DATABASE="airdrop"
```
# 跑签名程序
```bash
python3 run_signer.py
```

# 跑空投程序
```bash
python3 run_airdrop.py
```