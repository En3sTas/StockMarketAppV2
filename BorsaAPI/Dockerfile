# ─────────────────────────────────────────────
# Stage 1: Build
# ─────────────────────────────────────────────
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy project file and restore dependencies first (layer cache optimization)
COPY BorsaAPI.csproj ./
RUN dotnet restore

# Copy remaining source files
COPY . ./

# Publish in Release mode
RUN dotnet publish -c Release -o /app/publish --no-restore

# ─────────────────────────────────────────────
# Stage 2: Runtime
# ─────────────────────────────────────────────
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app

# Install missing native libraries required by .NET 10 Kestrel on Debian Trixie
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgssapi-krb5-2 \
    libkrb5-3 \
    && rm -rf /var/lib/apt/lists/*

# Copy published output from build stage
COPY --from=build /app/publish .

# Expose HTTP port (HTTPS is terminated by reverse proxy in production)
EXPOSE 8080

# Set environment variables for runtime
ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production

ENTRYPOINT ["dotnet", "BorsaAPI.dll"]

