// Cluster 28

package com.bht.saigonparking.common.util;

import com.google.protobuf.ByteString;
import com.google.protobuf.Internal;

/**
 * using this util class to encode & decode
 * to communicate between server and client
 * using protocol buffer of gRPC
 *
 * @author bht
 */
public final class ImageUtil {

    private ImageUtil() {
    }

    /**
     *
     * using from send's side
     * to encode image data
     * for sending image purpose
     */
    public static ByteString encodeImage(byte[] imageData) {
        return ByteString.copyFrom((imageData != null) ? imageData : Internal.EMPTY_BYTE_ARRAY);
    }

    /**
     *
     * using from receive's side
     * to decode image data
     * for reading image purpose
     */
    public static byte[] decodeImage(ByteString imageData) {
        return imageData.toByteArray();
    }

    /**
     *
     * using from receive's side
     * to check if the imageData received is empty or not
     */
    public static boolean isDecodedImageEmpty(byte[] imageData) {
        return imageData.length == 0;
    }
}

// Node: encodeImage
// Node: copyFrom
package com.bht.saigonparking.service.parkinglot.mapper;

import java.sql.Time;
import java.sql.Timestamp;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.mapstruct.Mapper;
import org.mapstruct.Named;
import org.mapstruct.NullValueMappingStrategy;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotInformation;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotType;
import com.bht.saigonparking.common.util.ImageUtil;
import com.bht.saigonparking.service.parkinglot.configuration.AppConfiguration;
import com.bht.saigonparking.service.parkinglot.service.extra.ImageService;
import com.google.protobuf.ByteString;

import lombok.Setter;

/**
 *
 * Mapper for the others & default object of each type
 *
 * Note that customized class and all of
 * its attributes, its methods should be declared as non-public
 * in order to hide this class and its methods, its attributes
 * from outside of mapper package
 *
 * @author bht
 */
@Component
@Setter(onMethod = @__(@Autowired))
@Mapper(componentModel = "spring",
        implementationPackage = AppConfiguration.BASE_PACKAGE + ".mapper.impl",
        nullValueMappingStrategy = NullValueMappingStrategy.RETURN_DEFAULT)
public abstract class CustomizedMapper {

    private ImageService imageService;

    public static final String DEFAULT_STRING_VALUE = "";
    public static final Short DEFAULT_SHORT_VALUE = 0;
    public static final Integer DEFAULT_INT_VALUE = 0;
    public static final Long DEFAULT_LONG_VALUE = 0L;
    public static final Double DEFAULT_DOUBLE_VALUE = 0.0;
    public static final Boolean DEFAULT_BOOL_VALUE = Boolean.FALSE;
    public static final ByteString DEFAULT_BYTE_STRING_VALUE = ByteString.EMPTY;

    public static final ParkingLotType DEFAULT_PARKING_LOT_TYPE = ParkingLotType.UNRECOGNIZED;
    public static final ParkingLotInformation DEFAULT_PARKING_LOT_INFORMATION = ParkingLotInformation.getDefaultInstance();

    @Named("toTimeString")
    public String toTimeString(@NotNull Time time) {
        return time.toString();
    }

    @Named("toTime")
    public Time toTime(@NotEmpty String timeString) {
        return Time.valueOf(timeString);
    }

    @Named("toTimestampString")
    public String toTimestampString(@NotNull Timestamp timestamp) {
        return timestamp.toString();
    }

    @Named("toTimestamp")
    public Timestamp toTimestamp(@NotEmpty String timestampString) {
        return Timestamp.valueOf(timestampString);
    }

    @Named("toEncodedParkingLotImage")
    public ByteString toEncodedParkingLotImage(@NotNull Integer parkingLotId) {
        return ImageUtil.encodeImage(imageService.getImage(
                "plot" + parkingLotId, ImageService.ImageExtension.JPG));
    }
}

// Node: toEncodedParkingLotImage
// Node: getImage
package com.bht.saigonparking.service.parkinglot.service.extra;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import lombok.Getter;

/**
 * This is util class for processing images purpose
 * such as get/save/delete images,
 * for using only in Saigon Parking Project here
 *
 * Used to store images on machine only
 * Currently using cloud storage: Amazon S3
 * to minimize task of server, minimize server storage
 *
 * Just use server to process only, not for storing, for example:
 * + communicate with RDBMS in Amazon RDS, via SSMS
 * + storing image, document in Amazon S3, via REST
 * + web-front end will interact with web-server on upper layer
 *
 * @author bht
 */
public interface ImageService {

    enum ImageExtension {
        JPG("jpg"),
        PNG("png");

        @Getter
        private final String extension;

        ImageExtension(String extension) {
            this.extension = extension;
        }
    }

    byte[] getImage(@NotEmpty String pathFromGalleryDir, @NotNull ImageExtension fileExtension);


    void saveImage(byte[] imageData, @NotEmpty String pathFromGalleryDir, @NotNull ImageExtension fileExtension);


    void deleteImage(@NotEmpty String pathFromGalleryDir, @NotNull ImageExtension fileExtension);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/service/extra/ImageService.java:for.<init>
// Node: JPG
// Node: PNG
// Node: ImageExtension
// Node: saveImage
// Node: deleteImage
package com.bht.saigonparking.service.parkinglot.service.extra;

import java.io.InputStream;

import javax.validation.constraints.NotEmpty;

/**
 *
 * common methods to interact with Amazon S3 Cloud Storage
 *
 * @author bht
 */
public interface S3Service {

    InputStream getFile(@NotEmpty String filePath, boolean warnOnFail);

    void saveFile(byte[] fileData, @NotEmpty String filePath, boolean warnOnFail);

    void deleteFile(@NotEmpty String filePath, boolean warnOnFail);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/service/extra/S3Service.java:S3Service.<init>
// Node: getFile
// Node: saveFile
// Node: deleteFile
package com.bht.saigonparking.service.parkinglot.service.extra.impl;

import java.io.IOException;
import java.io.InputStream;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.bht.saigonparking.service.parkinglot.service.extra.ImageService;
import com.bht.saigonparking.service.parkinglot.service.extra.S3Service;
import com.google.common.io.ByteStreams;
import com.google.protobuf.Internal;

import lombok.AllArgsConstructor;

/**
 *
 * this class implements all services relevant to processing image store on S3
 * S3 is a cloud storage approach for web-services, provided by amazon
 *
 * for clean code purpose,
 * using {@code @AllArgsConstructor} for Service class
 * it will {@code @Autowired} all attributes declared inside
 * hide {@code @Autowired} as much as possible in code
 * remember to mark all attributes as {@code private final}
 *
 * @author bht
 */
@Service
@Transactional
@AllArgsConstructor(onConstructor = @__(@Autowired))
public class ImageServiceImpl implements ImageService {

    private final S3Service s3Service;


    private static String toImagePath(@NotEmpty String pathFromGalleryDir, @NotNull ImageService.ImageExtension fileExtension) {
        return "gallery/" + pathFromGalleryDir + '.' + fileExtension.getExtension();
    }

    @Override
    public byte[] getImage(@NotEmpty String pathFromGalleryDir, @NotNull ImageService.ImageExtension fileExtension) {
        try (InputStream inputStream = s3Service.getFile(toImagePath(pathFromGalleryDir, fileExtension), false)) {
            return (inputStream != null) ? ByteStreams.toByteArray(inputStream) : Internal.EMPTY_BYTE_ARRAY;

        } catch (IOException e) {
            return Internal.EMPTY_BYTE_ARRAY;
        }
    }

    @Override
    public void saveImage(byte[] imageData, @NotEmpty String pathFromGalleryDir, @NotNull ImageService.ImageExtension fileExtension) {
        if (imageData != null && imageData.length > 0) {
            s3Service.saveFile(imageData, toImagePath(pathFromGalleryDir, fileExtension), true);
        }
    }

    @Override
    public void deleteImage(@NotEmpty String pathFromGalleryDir, @NotNull ImageService.ImageExtension fileExtension) {
        s3Service.deleteFile(toImagePath(pathFromGalleryDir, fileExtension), true);
    }
}

// Node: toImagePath
// Node: getExtension
// Node: try
package com.bht.saigonparking.service.parkinglot.service.extra.impl;

import java.io.IOException;
import java.io.InputStream;

import javax.validation.constraints.NotEmpty;

import org.apache.logging.log4j.Level;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.amazonaws.AmazonClientException;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.model.ObjectMetadata;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.parkinglot.service.extra.S3Service;
import com.google.common.io.ByteSource;

import lombok.AllArgsConstructor;

/**
 *
 * this class implements all services relevant to amazon S3
 * S3 is a cloud storage approach for web-services, provided by amazon
 *
 * for clean code purpose,
 * using {@code @AllArgsConstructor} for Service class
 * it will {@code @Autowired} all attributes declared inside
 * hide {@code @Autowired} as much as possible in code
 * remember to mark all attributes as {@code private final}
 *
 * @author bht
 */
@Service
@Transactional
@AllArgsConstructor(onConstructor = @__(@Autowired))
public class S3ServiceImpl implements S3Service {

    private final AmazonS3 amazonS3Client;

    @Qualifier("bucketName")
    private final String bucketName;

    @Override
    public InputStream getFile(@NotEmpty String filePath, boolean warnOnFail) {
        try {

            InputStream inputStream = amazonS3Client.getObject(bucketName, filePath).getObjectContent();
            LoggingUtil.log(Level.DEBUG, "SERVICE", "Success", String.format("getS3File(\"%s\")", filePath));
            return inputStream;

        } catch (AmazonClientException exception) {

            if (warnOnFail) {
                LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
                LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", String.format("getS3File(\"%s\")", filePath));
            }

            return null;
        }
    }

    @Override
    public void saveFile(byte[] fileData, @NotEmpty String filePath, boolean warnOnFail) {
        try (InputStream inputStream = ByteSource.wrap(fileData).openStream()) {

            ObjectMetadata metadata = new ObjectMetadata();
            metadata.setContentLength(fileData.length);
            amazonS3Client.putObject(bucketName, filePath, inputStream, metadata);

            LoggingUtil.log(Level.DEBUG, "SERVICE", "Success", String.format("saveS3File(\"%s\")", filePath));

        } catch (AmazonClientException | IOException exception) {

            if (warnOnFail) {
                LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
                LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", String.format("saveS3File(\"%s\")", filePath));
            }
        }
    }

    @Override
    public void deleteFile(@NotEmpty String filePath, boolean warnOnFail) {
        try {
            amazonS3Client.deleteObject(bucketName, filePath);

            LoggingUtil.log(Level.DEBUG, "SERVICE", "Success", String.format("deleteS3File(\"%s\")", filePath));

        } catch (AmazonClientException exception) {

            if (warnOnFail) {
                LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
                LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", String.format("deleteS3File(\"%s\")", filePath));
            }
        }
    }
}

// Node: getObject
// Node: getObjectContent
// Node: getS3File
// Node: wrap
// Node: openStream
// Node: ObjectMetadata
// Node: setContentLength
// Node: putObject
// Node: saveS3File
