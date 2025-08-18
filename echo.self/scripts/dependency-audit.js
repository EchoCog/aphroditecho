#!/usr/bin/env node

/**
 * Enhanced Dependency Audit Script
 * Part of EchoSelf's automated dependency management system
 */

import fs from "fs";
import path from "path";
import { execSync } from "child_process";
import process from "node:process";

function getPackageJson() {
  try {
    return JSON.parse(fs.readFileSync("package.json", "utf8"));
  } catch (error) {
    console.error("❌ Could not read package.json:", error.message);
    process.exit(1);
  }
}

function checkDependencyUsage(deps, searchDirs = ["app", "src"]) {
  const unusedDeps = [];
  const usageCount = {};

  for (const dep of Object.keys(deps)) {
    usageCount[dep] = 0;

    for (const dir of searchDirs) {
      if (!fs.existsSync(dir)) continue;

      try {
        // Search for import/require statements
        const result = execSync(
          `find ${dir} -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -exec grep -l "${dep}" {} \\; 2>/dev/null || true`,
          { encoding: "utf8" }
        );

        const files = result.split("\n").filter(f => f.trim());
        usageCount[dep] += files.length;
      } catch (error) {
        // Ignore grep errors
      }
    }

    if (usageCount[dep] === 0) {
      unusedDeps.push(dep);
    }
  }

  return { unusedDeps, usageCount };
}

function checkSecurityVulnerabilities() {
  try {
    console.log("🔍 Running security audit...");
    const result = execSync(
      'npm audit --json 2>/dev/null || echo "{\\"vulnerabilities\\":{}}"',
      { encoding: "utf8" }
    );
    const audit = JSON.parse(result);

    return {
      vulnerabilities: audit.vulnerabilities || {},
      summary: audit.metadata?.vulnerabilities || {},
    };
  } catch (error) {
    console.warn("⚠️ Could not run security audit:", error.message);
    return { vulnerabilities: {}, summary: {} };
  }
}

function generateReport(packageJson, dependencyAnalysis, securityAudit) {
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalDependencies: Object.keys(packageJson.dependencies || {}).length,
      totalDevDependencies: Object.keys(packageJson.devDependencies || {})
        .length,
      unusedDependencies: dependencyAnalysis.unusedDeps.length,
      securityVulnerabilities: Object.keys(securityAudit.vulnerabilities)
        .length,
    },
    details: {
      unusedDependencies: dependencyAnalysis.unusedDeps,
      dependencyUsage: dependencyAnalysis.usageCount,
      securityVulnerabilities: securityAudit.vulnerabilities,
      securitySummary: securityAudit.summary,
    },
  };

  return report;
}

function main() {
  console.log("📊 EchoSelf Dependency Audit Tool");
  console.log("==================================");

  const packageJson = getPackageJson();

  // Analyze dependencies
  console.log("🔍 Analyzing dependency usage...");
  const allDeps = {
    ...(packageJson.dependencies || {}),
    ...(packageJson.devDependencies || {}),
  };

  const dependencyAnalysis = checkDependencyUsage(allDeps);

  // Check security vulnerabilities
  const securityAudit = checkSecurityVulnerabilities();

  // Generate report
  const report = generateReport(packageJson, dependencyAnalysis, securityAudit);

  // Output results
  console.log("\n📋 Audit Results:");
  console.log(`  Total Dependencies: ${report.summary.totalDependencies}`);
  console.log(
    `  Total Dev Dependencies: ${report.summary.totalDevDependencies}`
  );
  console.log(`  Unused Dependencies: ${report.summary.unusedDependencies}`);
  console.log(
    `  Security Vulnerabilities: ${report.summary.securityVulnerabilities}`
  );

  if (report.details.unusedDependencies.length > 0) {
    console.log("\n⚠️ Potentially Unused Dependencies:");
    report.details.unusedDependencies.forEach(dep => {
      console.log(
        `  - ${dep} (usage count: ${report.details.dependencyUsage[dep]})`
      );
    });
  }

  if (Object.keys(report.details.securityVulnerabilities).length > 0) {
    console.log("\n🚨 Security Vulnerabilities Found:");
    console.log("  Run `npm audit` for detailed information.");
  }

  // Save report to maintenance logs
  const logsDir = ".maintenance-logs";
  if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir, { recursive: true });
  }

  const reportPath = path.join(logsDir, "dependency-analysis.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\n💾 Detailed report saved to: ${reportPath}`);

  // Exit with error code if issues found
  const hasIssues =
    report.summary.unusedDependencies > 0 ||
    report.summary.securityVulnerabilities > 0;
  process.exit(hasIssues ? 1 : 0);
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  main();
}

export {
  getPackageJson,
  checkDependencyUsage,
  checkSecurityVulnerabilities,
  generateReport,
};
