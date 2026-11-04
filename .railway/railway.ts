// Preparation only. Never apply/provision without separate deployment approval.
// Railway Free entitlement/credits must be checked privately before any apply.
import { defineRailway, github, preserve, project, service, volume } from "railway/iac";

export default defineRailway(() => {
  const data = volume("review-private-data", { region: "us-west2", sizeMB: 500 });
  const web = service("customer-service-review", {
    source: github("safiafares20073/customer-service-ai-agent", { branch: "main" }),
    build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile" },
    replicas: 1,
    healthcheck: "/healthz",
    healthcheckTimeout: 120,
    deploy: {
      region: "us-west2",
      requiredMountPath: "/var/lib/customer-service",
      restartPolicyType: "NEVER",
      sleepApplication: true,
      limitOverride: {
        containers: { cpu: 1, memoryBytes: 500000000, diskBytes: 1000000000 },
      },
    },
    volumeMounts: { "/var/lib/customer-service": data },
    env: {
      APP_ENV: "production",
      ENABLE_DEMO_AUTH: "false",
      UI_PROVIDER: "openai",
      HOSTED_DATA_DIR: "/var/lib/customer-service",
      PORT: "8080",
      OPENAI_MODEL: "gpt-6-luna",
      MODEL_PRICING_FILE: "/app/config/model_pricing.json",
      HOSTED_PAID_ENABLED: "false",
      HOSTED_GLOBAL_BUDGET_USD: "0",
      HOSTED_PRINCIPAL_BUDGET_USD: "0",
      HOSTED_APPROVAL_UNTIL: "0",
      HOSTED_REVIEWERS_JSON: preserve(),
      HOSTED_REVIEWER_EMAILS_JSON: preserve(),
      HOSTED_ORIGIN: preserve(),
      OIDC_ISSUER: preserve(),
      OIDC_METADATA_URL: preserve(),
      OIDC_CLIENT_ID: preserve(),
      OIDC_CLIENT_SECRET: preserve(),
      HOSTED_COOKIE_SECRET: preserve(),
      HOSTED_PRINCIPAL_SECRET: preserve(),
      OPENAI_API_KEY: preserve(),
      LLM_API_KEY: preserve(),
    },
  });
  return project("customer-service-review", { resources: [web, data] });
});
