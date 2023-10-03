FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install schedule
RUN pip install mechanize
COPY . .

# CMD ["cd", "marks"]
CMD ["python", "main.py"]
