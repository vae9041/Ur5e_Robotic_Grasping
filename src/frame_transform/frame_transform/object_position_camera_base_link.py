#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped
from tf2_ros import TransformListener, Buffer
from tf2_geometry_msgs import do_transform_point
from frame_transform.srv import FrameTransform

class ConversionFrameServer(Node):
    def __init__(self):
        super().__init__('frame_conversion_server')
        
        # TF2 setup
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Subscriber
        self.frame_sub = self.create_subscription(
            PointStamped,
            '/grasp_detection/object_position_camera_frame',
            self.conversion_callback,
            10
        )
        
        # Service server
        self.server = self.create_service(
            FrameTransform,
            '/get_position_base_link',
            self.handle_conversion
        )
        
        self.point_base_link = None
        
        self.get_logger().info('Frame conversion server ready')

    def conversion_callback(self, data):
        try:
            # Wait for transform to be available
            transform = self.tf_buffer.lookup_transform(
                'base_link',
                data.header.frame_id,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=1.0)
            )
            
            # Transform point from camera_optical_link to base_link
            self.point_base_link = do_transform_point(data, transform)
            
            self.get_logger().info(
                f'Transformed point: x={self.point_base_link.point.x:.3f}, '
                f'y={self.point_base_link.point.y:.3f}, '
                f'z={self.point_base_link.point.z:.3f}'
            )
            
        except Exception as e:
            self.get_logger().error(f'Transform failed: {e}')

    def handle_conversion(self, request, response):
        if self.point_base_link is not None:
            response.x_base_link_frame = self.point_base_link.point.x
            response.y_base_link_frame = self.point_base_link.point.y
            response.z_base_link_frame = self.point_base_link.point.z
            
            self.get_logger().info(
                f'Object position in base_link frame: '
                f'x={response.x_base_link_frame:.3f}, '
                f'y={response.y_base_link_frame:.3f}, '
                f'z={response.z_base_link_frame:.3f}'
            )
        else:
            self.get_logger().warn('No point transformed yet')
            response.x_base_link_frame = 0.0
            response.y_base_link_frame = 0.0
            response.z_base_link_frame = 0.0
        
        return response


def main(args=None):
    rclpy.init(args=args)
    conversion_server = ConversionFrameServer()
    
    try:
        rclpy.spin(conversion_server)
    except KeyboardInterrupt:
        print("Shutting down")
    finally:
        conversion_server.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()