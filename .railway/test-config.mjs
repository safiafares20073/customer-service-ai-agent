// Offline SDK evaluation only: no CLI login, plan, apply or network calls.
import assert from "node:assert/strict";
import test from "node:test";
import { createRailwayContext } from "railway/iac";
import definition from "./railway.ts";

const graph = definition(createRailwayContext({ environment: "production" }));
const web = graph.resources.find((r) => r.type === "service");
const data = graph.resources.find((r) => r.type === "volume");

test("one Docker service retains entrypoint, protected port and Free resource ceiling", () => {
  assert.equal(graph.resources.length, 2);
  assert.equal(web.build.builder, "DOCKERFILE");
  assert.equal(web.build.dockerfilePath, "Dockerfile");
  assert.equal(web.deploy.startCommand, undefined);
  assert.equal(web.deploy.preDeployCommand, undefined);
  assert.equal(web.deploy.numReplicas, 1);
  assert.deepEqual(web.deploy.limitOverride.containers,
    { cpu: 1, memoryBytes: 500000000, diskBytes: 1000000000 });
  assert.equal(web.variables.PORT.value, "8080");
});

test("single private volume is attached at the launcher's exact required path", () => {
  assert.equal(data.config.sizeMB, 500);
  const attached = web.volumeAttachments[data.name];
  assert.equal(attached.mountPath, "/var/lib/customer-service");
  assert.equal(attached.volume, data.address);
  assert.equal(data.config.region, web.deploy.region);
  assert.equal(web.deploy.requiredMountPath, attached.mountPath);
});

test("paid defaults are closed and secret values are preserved without source literals", () => {
  assert.equal(web.variables.APP_ENV.value, "production");
  assert.equal(web.variables.ENABLE_DEMO_AUTH.value, "false");
  assert.equal(web.variables.UI_PROVIDER.value, "openai");
  assert.equal(web.variables.HOSTED_PAID_ENABLED.value, "false");
  for (const key of ["HOSTED_GLOBAL_BUDGET_USD", "HOSTED_PRINCIPAL_BUDGET_USD",
    "HOSTED_APPROVAL_UNTIL"]) assert.equal(web.variables[key].value, "0");
  for (const key of ["OPENAI_API_KEY", "LLM_API_KEY", "OIDC_CLIENT_SECRET",
    "HOSTED_COOKIE_SECRET", "HOSTED_PRINCIPAL_SECRET", "HOSTED_REVIEWERS_JSON"]) {
    assert.equal(web.variables[key].type, "preserve");
    assert.equal(web.variables[key].value, undefined);
  }
});

test("health routing and bounded offline-safe restart policy do not require paid calls", () => {
  assert.equal(web.deploy.healthcheckPath, "/healthz");
  assert.equal(web.deploy.healthcheckTimeout, 120);
  assert.equal(web.deploy.restartPolicyType, "NEVER");
  assert.equal(web.deploy.sleepApplication, true);
  assert.equal(web.networking, undefined);
  assert.equal(web.source.repo, "safiafares20073/customer-service-ai-agent");
  assert.equal(web.source.branch, "main");
});
