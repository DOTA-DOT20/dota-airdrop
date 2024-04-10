# 导入原始数据
把项目主目录下的`airdrop.sql`文件导入mysql数据库中

# 安装依赖
 ```bash
 pip install -r requirements.txt
 ```

# 设置环境变量
```bash
cp .env.test .env
```
然后在.env文件中修改环境变量
# 跑签名程序
```bash
python3 run_signer.py
```

# 跑空投程序
```bash
python3 run_airdrop.py
```