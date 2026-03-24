FROM node:22-alpine

WORKDIR /workspace/frontend

COPY package*.json ./
RUN if [ -f package.json ]; then npm install; else echo "Angular app not generated yet"; fi

COPY . .

CMD ["sh", "-c", "if [ -f package.json ]; then npm start -- --host 0.0.0.0 --port 4200; else tail -f /dev/null; fi"]
