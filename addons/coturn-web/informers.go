/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

package main

import (
	"fmt"
	"log"

	corev1 "k8s.io/api/core/v1"

	"k8s.io/apimachinery/pkg/util/runtime"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/cache"
)

func StartEndpointsInformer(clientset *kubernetes.Clientset, addFunc, deleteFunc func(ep *corev1.Endpoints), updateFunc func(oldEp, newEp *corev1.Endpoints)) chan struct{} {
	// Create the shared informer factory and use the client to connect to
	// Kubernetes
	factory := informers.NewSharedInformerFactory(clientset, 0)

	// Get the informer for the right resource, in this case a Pod
	informer := factory.Core().V1().Endpoints().Informer()

	// Create a channel to stops the shared informer gracefully
	stopper := make(chan struct{})

	// Kubernetes serves an utility to handle API crashes
	defer runtime.HandleCrash()

	// This is the part where your custom code gets triggered based on the
	// event that the shared informer catches
	informer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			ep := obj.(*corev1.Endpoints)
			addFunc(ep)
		},
		DeleteFunc: func(obj interface{}) {
			ep := obj.(*corev1.Endpoints)
			deleteFunc(ep)
		},
		UpdateFunc: func(oldObj interface{}, newObj interface{}) {
			oldEp := oldObj.(*corev1.Endpoints)
			newEp := newObj.(*corev1.Endpoints)
			updateFunc(oldEp, newEp)
		},
	})

	// You need to start the informer, in my case, it runs in the background
	go informer.Run(stopper)
	log.Printf("started Endpoints Informer")

	if !cache.WaitForCacheSync(stopper, informer.HasSynced) {
		runtime.HandleError(fmt.Errorf("Timed out waiting for caches to sync"))
	}

	return stopper
}

func StartNodesInformer(clientset *kubernetes.Clientset, addFunc, deleteFunc func(node *corev1.Node), updateFunc func(oldNode, newNode *corev1.Node)) chan struct{} {
	// Create the shared informer factory and use the client to connect to
	// Kubernetes
	factory := informers.NewSharedInformerFactory(clientset, 0)

	// Get the informer for the right resource, in this case a Pod
	informer := factory.Core().V1().Nodes().Informer()

	// Create a channel to stops the shared informer gracefully
	stopper := make(chan struct{})

	// Kubernetes serves an utility to handle API crashes
	defer runtime.HandleCrash()

	// This is the part where your custom code gets triggered based on the
	// event that the shared informer catches
	informer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			node := obj.(*corev1.Node)
			addFunc(node)
		},
		DeleteFunc: func(obj interface{}) {
			node := obj.(*corev1.Node)
			deleteFunc(node)
		},
		UpdateFunc: func(oldObj interface{}, newObj interface{}) {
			oldNode := oldObj.(*corev1.Node)
			newNode := newObj.(*corev1.Node)
			updateFunc(oldNode, newNode)
		},
	})

	// You need to start the informer, in my case, it runs in the background
	go informer.Run(stopper)

	log.Printf("started Nodes Informer")

	if !cache.WaitForCacheSync(stopper, informer.HasSynced) {
		runtime.HandleError(fmt.Errorf("Timed out waiting for caches to sync"))
	}

	return stopper
}
