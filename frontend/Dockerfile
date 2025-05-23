# Stage 1: Build the application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock or pnpm-lock.yaml)
COPY package*.json ./
# If using pnpm, copy pnpm-lock.yaml
# COPY pnpm-lock.yaml .

# Install dependencies
# If using npm:
RUN npm install
# If using yarn:
# RUN yarn install
# If using pnpm:
# RUN npm install -g pnpm && pnpm install

# Copy the rest of the application code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy the built assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the Nginx configuration file
# Assuming nginx.conf for the frontend is in the frontend directory or a shared location
# For this setup, we will use a simple default Nginx config, 
# as the main nginx.conf in the root handles proxying.
# If a custom frontend-specific nginx config is needed, it should be copied here.
# COPY nginx.conf /etc/nginx/conf.d/default.conf 

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]

