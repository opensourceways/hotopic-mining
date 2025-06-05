FROM openeuler/openeuler:24.03

RUN groupadd -g 1001 pr \
    && useradd -u 1001 -g pr -s /bin/bash -m pr

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# CMD ["python", "app/main.py"]
