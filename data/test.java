/**
 * An event that is emitted when a container is idle if the container is configured to do so.
 * spring-kafka-3.0.9
 */
public class ListenerContainerIdleEvent extends KafkaEvent {
	// Retrieve the consumer.
	org.apache.kafka.clients.consumer.Consumer<?,?> getConsumer();
	// How long the container has been idle.
	long getIdleTime();
	// The id of the listener (if @KafkaListener) or the container bean name.
	String getListenerId();
	// The TopicPartitions the container is listening to.
	Collection<org.apache.kafka.common.TopicPartition> getTopicPartitions();
	// Return true if the consumer was paused at the time the idle event was published.
	boolean isPaused();
	String toString();
}