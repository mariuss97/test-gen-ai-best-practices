---
description: Best practices for Java Spring Boot backend development
applyTo: "**/*.java"
---

# Spring Boot backend development

Apply these rules only when the project uses Spring Boot. In a monorepo with
non-Spring Java projects, narrow `applyTo` to the backend folders, for example
`"projects/backend-*/**/*.java"`.

## Target stack

- Java 21 (21.0.9). Spring Boot 4.1.1, which brings Spring Framework 7,
  Jakarta EE 11 (Servlet 6.1), Spring Security 7, Hibernate ORM 7 and
  Jackson 3.
- Use the dependency versions managed by the Spring Boot BOM. Do not pin
  versions of managed dependencies. Keep the Spring Boot version in one place
  (parent, BOM property or version catalog).
- Write code for Spring Boot 4. Do not suggest Spring Boot 2 or 3 APIs or
  `javax.*` imports; use `jakarta.*`.

## Java 21

- Use modern language features where they make code clearer: records for DTOs
  and value objects, pattern matching for `instanceof` and `switch`, switch
  expressions, text blocks, sequenced collections.
- Do not use preview features.
- Virtual threads (`spring.threads.virtual.enabled=true`) suit blocking I/O
  workloads. Enable them only as a deliberate team decision, not per class.

## Spring Boot 4 specifics

- Use the technology-specific starters, for example
  `spring-boot-starter-webmvc` instead of the deprecated alias
  `spring-boot-starter-web`. Tests need the matching `spring-boot-starter-*-test`
  module, for example `spring-boot-starter-webmvc-test`.
- Jackson 3 lives in `tools.jackson.*` (group `tools.jackson`). Only the
  annotations stay in `com.fasterxml.jackson.annotation`. Use
  `JsonMapperBuilderCustomizer` and `@JacksonComponent` instead of
  `Jackson2ObjectMapperBuilderCustomizer` and `@JsonComponent`.
- Mark nullability with JSpecify: `org.jspecify.annotations.Nullable`, not
  `org.springframework.lang.Nullable` or `javax.annotation.*`. Values such as
  `RestClient` response bodies can be null; check them.
- Use `RestClient` or HTTP interface clients (`@HttpExchange`) for outgoing
  HTTP calls. Do not use `RestTemplate` in new code.
- Use the retry support in Spring Framework 7 instead of adding Spring Retry.
- Use Tomcat (default) or Jetty. Undertow is no longer supported.

## General

- Make only high-confidence suggestions when reviewing code changes.
- Write maintainable code. Comment on why a design decision was made, not on
  what the code does.
- Handle edge cases and write clear exception handling.
- When you add a library or external dependency, state its purpose in a
  comment.
- Follow what the project already uses (build tool, config format, libraries)
  before introducing something new.

## Dependency injection

- Use constructor injection for all required dependencies.
- Declare dependency fields as `private final`.
- Do not use field injection (`@Autowired` on fields).

## Configuration

- Externalize configuration in `application.properties` or `application.yml`,
  matching what the project already uses.
- Use Spring profiles for environments (dev, test, prod).
- Bind configuration type-safely with `@ConfigurationProperties`.
- Never commit secrets. Read them from environment variables or a secret
  manager.

## Code organization

- Organize packages by feature or domain, not by layer.
- Keep controllers thin, services focused and repositories simple.
- Make utility classes `final` with a private constructor.

## Web layer

- Use DTOs for requests and responses, preferably Java records. Do not expose
  JPA entities in the API.
- Validate request bodies and parameters with Bean Validation (`@Valid`,
  `@NotNull`, `@Size`, and so on).
- Handle errors in one `@RestControllerAdvice`, including
  `MethodArgumentNotValidException`. Return `ProblemDetail` (RFC 9457) with a
  fitting HTTP status.
- Use the correct HTTP status codes, for example `201 Created` for new
  resources and `404 Not Found` for missing ones.

## Service layer

- Put business logic in `@Service` classes.
- Keep services stateless and testable.
- Inject repositories through the constructor.
- Use domain IDs or DTOs in service method signatures. Do not expose
  repository entities unless necessary.
- Define transaction boundaries with `@Transactional` on service methods. Use
  `@Transactional(readOnly = true)` for read-only operations.

## Persistence

- Use Spring Data JPA or `NamedParameterJdbcTemplate`. Always use parameterized
  queries to prevent SQL injection.
- Avoid N+1 queries. Use fetch joins or entity graphs where related data is
  needed.
- Set `spring.jpa.open-in-view=false`, so database access stays in the service
  layer.
- Manage schema changes with migrations (Flyway or Liquibase, matching the
  project). Do not rely on `ddl-auto` outside local development.

## Logging

- Use SLF4J for all logging:
  `private static final Logger logger = LoggerFactory.getLogger(MyClass.class);`
- Do not use a concrete implementation (Logback, Log4j2) or
  `System.out.println()` directly.
- Use parameterized logging: `logger.info("User {} logged in", userId);`
- Never log secrets or personal data.

## Testing

- Write tests with JUnit Jupiter (version managed by the Spring Boot BOM) and
  AssertJ.
- Prefer slice tests: `@WebMvcTest` for controllers, `@DataJpaTest` for
  repositories. Use `@SpringBootTest` only for real integration tests. In
  Spring Boot 4 the slice annotations live in per-technology packages, for
  example `org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest` and
  `org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest`.
- Mock Spring beans with `@MockitoBean` and `@MockitoSpyBean`. `@MockBean` and
  `@SpyBean` were removed in Spring Boot 4. Plain Mockito `@Mock` fields need
  `@ExtendWith(MockitoExtension.class)`.
- `@SpringBootTest` no longer provides `TestRestTemplate` or `WebTestClient`
  automatically. Add `@AutoConfigureMockMvc` (package
  `org.springframework.boot.webmvc.test.autoconfigure`) for MockMvc.
- Run integration tests against real dependencies with Testcontainers, for
  example the same database as in production.
- Name integration tests `*IT`, so Maven Failsafe runs them in `verify`.

## Build and verification

- After adding or changing code, check that the project still builds.
- Maven: run `./mvnw verify` (use the wrapper). `package` skips Failsafe
  integration tests (`*IT`).
- Gradle: run `./gradlew build`. The Spring Boot 4 Gradle plugin needs
  Gradle 8.14 or later.
- All tests must pass as part of the build.
- Use `package` or `test` only as faster, focused commands, not as the final
  check.

## Useful commands

| Gradle | Maven | Description |
|--------|-------|-------------|
| `./gradlew bootRun` | `./mvnw spring-boot:run` | Run the application |
| `./gradlew build` | `./mvnw verify` | Build and run all tests |
| `./gradlew test` | `./mvnw test` | Run tests |
| `./gradlew bootJar` | `./mvnw spring-boot:repackage` | Package the application as a JAR |
| `./gradlew bootBuildImage` | `./mvnw spring-boot:build-image` | Package the application as a container image |

<!--
Based on instructions/springboot.instructions.md (commit 942a83b0a080,
2026-10-14) and the references of skills/spring-boot-4-migration (commit
f65ff3955a6b, 2026-10-22) from https://github.com/github/awesome-copilot,
adapted and extended for this team. Copyright GitHub, Inc., MIT license, see
docs/third-party-licenses/awesome-copilot-LICENSE. Official sources: the
Spring Boot 4.0 Migration Guide and Release Notes on the Spring Boot wiki.
-->
