# syntax=docker/dockerfile:1
ARG MAVEN_IMAGE=crpi-wbg5vm8h2xypwe6e.cn-chengdu.personal.cr.aliyuncs.com/gpufusion/maven:3.9-eclipse-temurin-17
ARG JRE_IMAGE=eclipse-temurin:17-jre
FROM ${MAVEN_IMAGE} AS build
WORKDIR /src
COPY pom.xml .
COPY maven-settings.xml /root/.m2/settings.xml
COPY user-service/pom.xml user-service/pom.xml
COPY inventory-service/pom.xml inventory-service/pom.xml
COPY order-service/pom.xml order-service/pom.xml
COPY gateway/pom.xml gateway/pom.xml
COPY recommend-bff/pom.xml recommend-bff/pom.xml
COPY user-service/src user-service/src
COPY inventory-service/src inventory-service/src
COPY order-service/src order-service/src
COPY gateway/src gateway/src
COPY recommend-bff/src recommend-bff/src
RUN mvn -B -s /root/.m2/settings.xml -pl user-service -am package -DskipTests

FROM ${JRE_IMAGE}
WORKDIR /app
COPY --from=build /src/user-service/target/*.jar /app/app.jar
ENV JAVA_OPTS="-Xms128m -Xmx384m"
EXPOSE 8080
ENTRYPOINT ["sh","-c","java $JAVA_OPTS -jar /app/app.jar"]
