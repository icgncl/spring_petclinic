FROM eclipse-temurin:17-jdk-jammy as build
WORKDIR /workspace/app
COPY . .
RUN ./mvnw clean package -DskipTests

FROM eclipse-temurin:17-jdk-jammy
WORKDIR /app
COPY --from=build /workspace/app/target/spring-petclinic-*.jar app.jar
ENTRYPOINT ["java","-jar","/app/app.jar"]

