FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install mechanize schedule

COPY . .

# CMD ["cd", "marks"]
CMD ["ls"]
CMD ["python", "main.py"]
