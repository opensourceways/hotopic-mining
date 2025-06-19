FROM openeuler/openeuler:24.03

RUN yum install shadow-utils python3-pip -y
RUN groupadd -g 1001 hotopic \
    && useradd -u 1001 -g hotopic -s /bin/bash -m hotopic

# 设置时区环境变量
ENV TZ=Asia/Shanghai
# 创建时区软链接并写入时区名称
RUN ln -sf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R hotopic:hotopic /app

USER hotopic

CMD ["python3", "-m", "hotopic.main"]
