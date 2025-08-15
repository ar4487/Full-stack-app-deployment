FROM nginx:alpine

# Add labels for better maintainability
LABEL maintainer="abhispeaks55@gmail.com>"
LABEL description="Frontend container for Notes application"

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static files
COPY . /usr/share/nginx/html

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80 || exit 1

EXPOSE 80
