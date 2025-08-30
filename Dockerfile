FROM node:22-slim

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* /app/

# Install dependencies
RUN npm install

# Copy source code
COPY . /app/

# Expose Vite dev server port
EXPOSE 5173

# Run Vite in dev mode, accessible outside container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
